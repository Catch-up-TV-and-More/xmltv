#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import os
import glob
import pytz
import xmltv
import subprocess
from datetime import datetime, timedelta

from channels import COUNTRIES_CHANNELS

SCRIPTS_DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/'
ROOT_DIRECTORY = SCRIPTS_DIRECTORY + '../'
RAW_DIRECTORY = ROOT_DIRECTORY + 'raw/'

# The date format used in XMLTV (the %Z will go away in 0.6)
DATE_FORMAT = '%Y%m%d%H%M%S %Z'
DATE_FORMAT_NOTZ = '%Y%m%d%H%M%S'
TODAY = datetime.now()

TEST_MODE = False

GRABBERS = {
    'tv_grab_fr_telerama': {
        'raw_min_size': 600000 if not TEST_MODE else 1000,
        'raw': 'tv_guide_fr_telerama{}.xml',
        'tz': 'Europe/Paris',
        'run_cmd': [
            SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama',
            '--config-file',
            SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama.conf' if not TEST_MODE else SCRIPTS_DIRECTORY + 'tv_grab_fr_telerama/tv_grab_fr_telerama_test.conf',
            '--no_htmltags',
            '--casting',
            '--days',
            '1',
            '--offset',
            'myoffset',
            '--output',
            'myoutput'
        ],
        'allowed_offsets': [0, 1, 2, 3, 4, 5, 6, 7]
    },
    'tv_grab_uk_tvguide': {
        'raw_min_size': 150000 if not TEST_MODE else 1000,
        'raw': 'tv_guide_uk_tvguide{}.xml',
        'tz': 'Europe/London',
        'run_cmd': [
            SCRIPTS_DIRECTORY + 'tv_grab_uk_tvguide/tv_grab_uk_tvguide',
            '--config-file',
            SCRIPTS_DIRECTORY + 'tv_grab_uk_tvguide/tv_grab_uk_tvguide.conf' if not TEST_MODE else SCRIPTS_DIRECTORY + 'tv_grab_uk_tvguide/tv_grab_uk_tvguide_test.conf',
            '--days',
            '1',
            '--offset',
            'myoffset',
            '--output',
            'myoutput'
        ],
        'allowed_offsets': [0, 1, 2, 3, 4, 5, 6, 7]
    },
    'tv_grab_it': {
        'raw_min_size': 150000 if not TEST_MODE else 1000,
        'raw': 'tv_guide_it{}.xml',
        'tz': 'Europe/Rome',
        'run_cmd': [
            SCRIPTS_DIRECTORY + 'tv_grab_it/tv_grab_it',
            '--config-file',
            SCRIPTS_DIRECTORY + 'tv_grab_it/tv_grab_it.conf' if not TEST_MODE else SCRIPTS_DIRECTORY + 'tv_grab_it/tv_grab_it_test.conf',
            '--days',
            '1',
            '--offset',
            'myoffset',
            '--output',
            'myoutput'
        ],
        'allowed_offsets': [0, 1, 2, 3, 4, 5, 6]
    }
}


def compute_md5(filepath):
    """Compute MDH hash of the file."""
    try:
        with open(filepath, "rb") as f:
            file_md5 = hashlib.md5()
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                file_md5.update(chunk)

            return file_md5.hexdigest()
    except Exception as e:
        raise RuntimeError("Failed to compute MD5 of file {} ({})".format(filepath, e))


def remove_root_xmltv_files():
    """In root directory, remove all XMLTV files."""
    print('\n# Remove all XMLTV files in root directory', flush=True)
    for f in glob.glob(ROOT_DIRECTORY + '*.xml'):
        os.remove(f)
    for f in glob.glob(ROOT_DIRECTORY + '*_md5.txt'):
        os.remove(f)


def remove_old_raw_files():
    """In 'raw' directory, remove old XMLTV and log files."""
    print('\n# Remove old XMLTV and log files of raw directory', flush=True)
    subexpr_to_remove = []
    for delta in range(3, 20):
        subexpr_to_remove.append((TODAY - timedelta(days=delta)).strftime("%Y%m%d"))
    for f in glob.glob(RAW_DIRECTORY + '*'):
        for expr in subexpr_to_remove:
            if expr in f:
                print('\t* Remove file ' + f, flush=True)
                os.remove(f)


def update_raw_files():
    """Update raw XMLTV files from grabbers."""
    print('\n# Update raw XMLTV files from grabbers', flush=True)
    my_env = os.environ.copy()
    my_env['HOME'] = SCRIPTS_DIRECTORY
    for delta in range(0, 8):
        day_to_grab = TODAY + timedelta(days=delta)
        print('\t* Grab TV guides of day {}'.format(day_to_grab.strftime("%d/%m/%Y")), flush=True)
        for grabber, grabber_infos in GRABBERS.items():
            if delta not in grabber_infos['allowed_offsets']:
                continue
            xmltv_fp = RAW_DIRECTORY + grabber_infos['raw'].format('_' + day_to_grab.strftime("%Y%m%d"))
            print('\t\t- Grab TV guide of {} grabber in {}'.format(grabber, xmltv_fp), flush=True)
            run_cmd = True
            if delta == 1:  # If delta is 1, force grabber to run (fix issue #7)
                print('\t\t\t* Force file update (delta is 1) --> run grabber', flush=True)
            elif os.path.exists(xmltv_fp):
                xmltv_file_size = os.path.getsize(xmltv_fp)
                if xmltv_file_size < grabber_infos['raw_min_size']:
                    print('\t\t\t* This file already exists but its size is small 0_o ({} bytes) --> run grabber again'.format(xmltv_file_size), flush=True)
                else:
                    print('\t\t\t* This file already exists (size: {} bytes) --> Nothing to do'.format(xmltv_file_size), flush=True)
                    run_cmd = False
            if run_cmd:
                stdout_f = open(xmltv_fp + '_stdout_stderr.log', 'w')
                cmd = grabber_infos['run_cmd']
                cmd[-1] = xmltv_fp
                cmd[-3] = str(delta)
                print('\t\t\t* Run cmd:', ' '.join(cmd), flush=True)
                subprocess.run(cmd, env=my_env, stdout=stdout_f, stderr=stdout_f)
                stdout_f.close()
                try:
                    final_size = os.path.getsize(xmltv_fp)
                except Exception:
                    final_size = 0
                print('\t\t\t* Final file size: {} bytes'.format(final_size), flush=True)


def parse_raw_xmltv_files():
    """Parse all xmltv files to deserialize info in dict."""
    print('\n# Parse all raw XMLTV files', flush=True)

    all_channels = {}  # Key: channel id in xmltv file, Value: channel dict
    all_data = {}  # Key: grabber, Value: data dict
    all_programmes = {}  # Key: channel id, Value: List of dict programme with UTC time
    all_programmes_local = {}  # Key: channel id, Value: List of dict programme with local time

    for grabber, grabber_infos in GRABBERS.items():
        print('\n\t* Processing of {} grabber\'s raw files:'.format(grabber), flush=True)
        for offset in range(-10, 20):
            date = TODAY + timedelta(days=offset)
            xmltv_fp = RAW_DIRECTORY + grabber_infos['raw'].format('_' + date.strftime("%Y%m%d"))
            if not os.path.exists(xmltv_fp):
                continue
            print('\t\t* Parse {} file'.format(xmltv_fp), flush=True)

            # Deserialize xmltv file
            try:
                data = xmltv.read_data(xmltv_fp)
                channels = xmltv.read_channels(xmltv_fp)
                programmes = xmltv.read_programmes(xmltv_fp)
            except Exception as e:
                print('\t\t\t- This file seems to be corrupt :-/, delete it ({})'.format(e), flush=True)
                os.remove(xmltv_fp)
                continue

            # Data
            if grabber not in all_data:
                all_data[grabber] = data

            # Channels
            print('\t\t\t- This file contains {} channels'.format(len(channels)), flush=True)
            for channel in channels:
                channel_id = channel['id']
                if channel_id not in all_channels:
                    all_channels[channel_id] = channel
                if channel_id not in all_programmes:
                    all_programmes[channel_id] = []
                if channel_id not in all_programmes_local:
                    all_programmes_local[channel_id] = []

            # Programmes

            # If there is no programme, delete this raw xmltv file
            if not programmes:
                print('\t\t\t- This file does not contain any TV shows :-/, delete it', flush=True)
                os.remove(xmltv_fp)
            else:
                print('\t\t\t- This file contains {} TV shows'.format(len(programmes)), flush=True)
                for programme in programmes:
                    channel_id = programme['channel']
                    all_programmes_local[channel_id].append(dict(programme))

                    # Replace local datetime by UTC datetime
                    programme_utc = dict(programme)
                    for elt in ['start', 'stop']:
                        if elt not in programme_utc:
                            continue
                        s = programme_utc[elt]

                        # Remove timezone part to get %Y%m%d%H%M%S format
                        s = s.split(' ')[0]

                        # Get the naive datetime object
                        d = datetime.strptime(s, DATE_FORMAT_NOTZ)

                        # Add correct timezone
                        tz = pytz.timezone(grabber_infos['tz'])
                        d = tz.localize(d)

                        # Convert to UTC timezone
                        utc_tz = pytz.UTC
                        d = d.astimezone(utc_tz)

                        # Finally replace the datetime with the UTC one
                        s = d.strftime(DATE_FORMAT_NOTZ)
                        # print('Replace {} by {}'.format(programme_utc[elt], s))
                        programme_utc[elt] = s

                    all_programmes[channel_id].append(dict(programme_utc))

    return (all_data, all_channels, all_programmes, all_programmes_local)


def generate_new_xmltv_files(all_data, all_channels, all_programmes, all_programmes_local):
    """In root directory, generate all new XMLTV files."""
    print('\n# Generate new XMLTV files in root directory', flush=True)
    for country_code, country_infos in COUNTRIES_CHANNELS.items():
        print('\n\t* Processing of {} country'.format(country_code), flush=True)

        # Write full xmltv file
        for fp_prefix in ['', '_local']:
            dst_fp = ROOT_DIRECTORY + country_infos['dst'].format(fp_prefix)
            print('\t\t- Write full{} xmltv file in {}'.format(fp_prefix, os.path.basename(dst_fp)), flush=True)
            w = xmltv.Writer()

            # Add channels
            for channel_id in country_infos['channels']:
                if channel_id in all_channels:
                    w.addChannel(all_channels[channel_id])

            # Add programmes
            if fp_prefix == '_local':
                programmes = all_programmes_local
            else:
                programmes = all_programmes

            cnt = 0
            for channel_id in country_infos['channels']:
                if channel_id in programmes:
                    for programme in programmes[channel_id]:
                        w.addProgramme(programme)
                        cnt += 1

            if cnt == 0:
                print('\t\t* This file does not contain any TV shows :-/, do not write it', flush=True)
                continue

            # Write XMLTV file
            with open(dst_fp, 'wb') as f:
                w.write(f, pretty_print=True)
            print('\t\t\t- Final file contains {} TV shows'.format(cnt), flush=True)

        # Write one day xmltv files
        for offset in range(-2, 8):
            date = TODAY + timedelta(days=offset)
            date_s = date.strftime("%Y%m%d")

            for fp_prefix in ['', '_local']:
                dst_fp = ROOT_DIRECTORY + country_infos['dst'].format(fp_prefix + '_' + date_s)
                print('\t\t- Write day {} in {}'.format(date_s, os.path.basename(dst_fp)), flush=True)
                w = xmltv.Writer()

                # Add channels
                for channel_id in country_infos['channels']:
                    if channel_id in all_channels:
                        w.addChannel(all_channels[channel_id])

                # Add programmes
                if fp_prefix == '_local':
                    programmes = all_programmes_local
                else:
                    programmes = all_programmes

                cnt = 0
                for channel_id in country_infos['channels']:
                    if channel_id in programmes:
                        for p in programmes[channel_id]:
                            add_it = False
                            if 'start' in p and 'stop' in p:
                                start_s = p['start'][0:8]
                                stop_s = p['stop'][0:8]
                                if start_s == date_s or stop_s == date_s:
                                    add_it = True
                            else:
                                add_it = True
                            if add_it:
                                w.addProgramme(p)
                                cnt = cnt + 1

                with open(dst_fp, 'wb') as f:
                    w.write(f, pretty_print=True)
                print('\t\t\t- Final file contains {} TV shows'.format(cnt), flush=True)

    print('\n\t* Merge all country tv guides in tv_guide_all.xml', flush=True)

    w = xmltv.Writer()

    # Add all channels
    for channel_id, channel in all_channels.items():
        w.addChannel(channel)

    # Add all programmes
    cnt = 0
    for channel_id, programmes in all_programmes.items():
        for p in programmes:
            w.addProgramme(p)
            cnt = cnt + 1

    with open(ROOT_DIRECTORY + 'tv_guide_all.xml', 'wb') as f:
        w.write(f, pretty_print=True)
    print('\t\t- Final file contains {} TV shows'.format(cnt), flush=True)

    print('\n\t* Merge all country tv guides in tv_guide_all_local.xml', flush=True)

    w = xmltv.Writer()

    # Add all channels
    for channel_id, channel in all_channels.items():
        w.addChannel(channel)

    # Add all programmes
    cnt = 0
    for channel_id, programmes in all_programmes_local.items():
        for p in programmes:
            w.addProgramme(p)
            cnt = cnt + 1

    with open(ROOT_DIRECTORY + 'tv_guide_all_local.xml', 'wb') as f:
        w.write(f, pretty_print=True)
    print('\t\t- Final file contains {} TV shows'.format(cnt), flush=True)


def generate_root_xmltv_files_md5():
    """For each xmltv files in root, generate corresponding md5 file."""
    print('\n# Compute MD5 hash of new XMLTV files', flush=True)
    for f in glob.glob(ROOT_DIRECTORY + '*.xml'):
        try:
            md5 = compute_md5(f)
            dst_fp = f.replace('.xml', '_md5.txt')
            with open(dst_fp, 'w') as f:
                f.write(md5)
        except Exception as e:
            print('\t- Failed to create MD5 file of {} ({})'.format(f, e), flush=True)


def main():
    print('\n# Start script at', datetime.now().strftime("%d/%m/%Y %H:%M:%S"), flush=True)
    remove_root_xmltv_files()
    remove_old_raw_files()
    update_raw_files()
    (all_data, all_channels, all_programmes, all_programmes_local) = parse_raw_xmltv_files()
    generate_new_xmltv_files(all_data, all_channels, all_programmes, all_programmes_local)
    generate_root_xmltv_files_md5()
    print('\n# Exit script at', datetime.now().strftime("%d/%m/%Y %H:%M:%S"), flush=True)


if __name__ == '__main__':
    main()
