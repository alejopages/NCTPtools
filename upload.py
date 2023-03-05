from os.path import join, exists
from os import listdir
import json
from datetime import date


def __write_id_to_results(results_dir_path, key, id):
    for result_file in listdir(results_dir_path):
        with open(path := join(results_dir_path, result_file), 'r') as result_file:
            payload = json.load(result_file)
            payload[key] = id
        with open(path, 'w') as result_file:
            json.dump(payload, result_file)


def __write_variety_id_to_results(results_dir_path, variety_name, id):
    for site_type in listdir(results_dir_path):
        for fips in listdir(site_type_path := join(results_dir_path, site_type)):
            for result_file in listdir(fips_path := join(site_type_path, fips)):
                with open(path := join(fips_path, result_file), 'r') as result_file:
                    payload = json.load(result_file)
                    if payload.get('name').strip() != variety_name.strip():
                        continue
                    payload['variety_id'] = id
                with open(path, 'w') as result_file:
                    json.dump(payload, result_file)


def sites(cli):
    for site_type in listdir((sites_basepath := join(cli.args.inpath, 'trial_sites'))):
        for fips_json in listdir(site_type_path := join(sites_basepath, site_type)):
            with open((path := join(site_type_path, fips_json)), 'r+') as sites_file:
                payload = json.load(sites_file)
            if payload.get('id') is not None and cli.args.rewrite:
                try:
                    resp = cli.client.site.delete(payload.get('id'))
                except Exception as e:
                    pass
                del(payload['id'])
            payload['harvest_year_pub_id'] = cli.args.year_id
            if payload.get('published_at') in ['', None]:
                payload['published_at'] = str(date.today())
            try:
                if payload.get('id') is None:
                    resp = cli.client.site.store(payload)
                else:
                    resp = cli.client.site.update(payload.get('id'), payload)
            except Exception as e:
                cli.write_to_manifest("WRITE_EXCEPTION", path, e)
                continue

            id = resp.json().get('id')
            if id is None:
                cli.write_to_manifest(
                    "WRITE_FAILED", path, resp.status_code, resp.reason, resp.json())
                continue

            payload['id'] = id

            with open((path := join(site_type_path, fips_json)), 'w') as sites_file:
                json.dump(payload, sites_file)

            if exists(results_path := join(cli.args.inpath, 'results', site_type, fips_json[:5])):
                __write_id_to_results(results_path, 'trial_site_id', id)


def varieties(cli):
    for variety_file in listdir((varieties_basepath := join(cli.args.inpath, 'varieties'))):
        with open((path := join(varieties_basepath, variety_file)), 'r+') as varieties_file:
            payload = json.load(varieties_file)
        if payload.get('id') is not None and cli.args.rewrite:
            try:
                cli.client.variety.delete(payload.get('id'))
            except Exception:
                pass
            del(payload['id'])
        
        payload['crop_harvest_year_publication_id'] = cli.args.year_id
        payload['aquisition_year'] = cli.args.year
        
        if payload.get('published_at') in ['', None]:
            payload['published_at'] = str(date.today())

        try:
            if payload.get('id') is None:
                resp = cli.client.variety.store(payload)
            else:
                resp = cli.client.variety.update(payload.get('id'), payload)
        except Exception as e:
            cli.write_to_manifest("WRITE_EXCEPTION", path, e)
            continue

        id = resp.json().get('id')
        if id is None:
            cli.write_to_manifest("WRITE_FAILED", path,
                                  resp.status_code, resp.reason, resp.json())
            continue
        payload['id'] = id

        with open((path := join(varieties_basepath, variety_file)), 'w') as varieties_file:
            json.dump(payload, varieties_file)

        __write_variety_id_to_results(
            join(cli.args.inpath, 'results'), payload.get('name'), id)


def results(cli):
    for site_type in listdir((results_basepath := join(cli.args.inpath, 'results'))):
        for fips in listdir(results_site_type_path := join(results_basepath, site_type)):
            for results_filename in listdir(payload_filepath := join(results_site_type_path, fips)):
                with open((path := join(payload_filepath, results_filename)), 'r+') as resuts_file:
                    payload = json.load(resuts_file)

                if payload.get('id') is not None and cli.args.rewrite:
                    try:
                        cli.client.results.delete(payload.get('id'))
                    except Exception as e:
                        pass
                    del(payload['id'])
                if payload.get('trial_site_id') is None or payload.get('variety_id') is None:
                    cli.write_to_manifest("WRITE_IGNORED",
                                          path, "Missing trial site and/or variety id")
                    continue

                try:
                    if payload.get('id') is None:
                        resp = cli.client.results.store(payload)
                    else:
                        resp = cli.client.results.update(payload.get('id'), payload)
                except Exception as e:
                    cli.write_to_manifest("WRITE_EXCEPTION", path, e)
                    continue

                id = resp.json().get('id')
                if id is None:
                    cli.write_to_manifest(
                        "WRITE_FAILED", path, resp.status_code, resp.reason, resp.json())
                    continue

                payload['id'] = id

                with open((path := join(payload_filepath, results_filename)), 'w') as resuts_file:
                    json.dump(payload, resuts_file)


def all(cli):
    sites(cli)
    varieties(cli)
    results(cli)
