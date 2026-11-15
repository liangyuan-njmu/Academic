#!/usr/bin/env python3
"""Best-effort journal-cover downloader for the GitHub Pages build.

Only stores images whose source is linked to a verified journal/issue record.
If a publisher blocks access or a source is unavailable, it leaves a clear
fallback on the webpage; it never substitutes an unrelated issue's cover.
"""
from __future__ import annotations
import io
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import argparse

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT=Path(__file__).resolve().parents[1]
ENTRIES=json.loads((ROOT/'cover_sources.json').read_text(encoding='utf-8'))
ASSETS=ROOT/'assets'/'covers'
ASSETS.mkdir(parents=True, exist_ok=True)
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; academic-homepage-cover-fetcher/1.0; educational use)'}
ses=requests.Session();ses.headers.update(HEADERS)


def discover_issue_cover(page:str, journal:str)->str:
    try:
        r=ses.get(page,timeout=15);r.raise_for_status()
    except requests.RequestException:
        return ''
    doc=BeautifulSoup(r.text,'html.parser')
    candidates=[]
    for el in doc.select('img,source'):
        alt=(el.get('alt') or '').lower()
        urls=[el.get(x) or '' for x in ('src','data-src','data-original','data-lazy-src')]
        if el.get('srcset'):
            urls.append((el.get('srcset') or '').split(',')[0].split(' ')[0])
        for u in urls:
            u=urljoin(r.url,u)
            if 'cover' not in (u+' '+alt).lower() or urlparse(u).scheme!='https':
                continue
            if any(t in (u+' '+alt).lower() for t in ['logo','banner','advert','avatar']):continue
            score=0
            if 'issue' in u.lower():score+=3
            if 'cover' in u.lower():score+=2
            if 'cover' in alt:score+=2
            if 'silverchair' in u.lower() or 'jci' in u.lower():score+=1
            # prevent loading a generic banner if there is no issue reference
            if 'Cancer Discovery'==journal and 'cancerdiscovery' in u.lower():score+=4
            if 'Cancer Research'==journal and 'cancerres' in u.lower():score+=4
            candidates.append((score,u))
    candidates.sort(reverse=True)
    return candidates[0][1] if candidates and candidates[0][0]>=4 else ''


def fetch_image(u):
    if not u.startswith('https://'):
        raise RuntimeError('Unsupported scheme')
    with ses.get(u,timeout=25,stream=True) as response:
        response.raise_for_status()
        data=bytearray()
        for chunk in response.iter_content(128*1024):
            data.extend(chunk)
            if len(data)>12*1024*1024:raise RuntimeError('Image >12MB')
    try:
        img=Image.open(io.BytesIO(data));img.load()
    except (UnidentifiedImageError,OSError):
        raise RuntimeError('Not an image')
    if img.width<100 or img.height<120:
        raise RuntimeError('Too small to be a journal cover')
    # Cover images are portrait; reject very wide page banners.
    if img.width/img.height>1.30:
        raise RuntimeError('Wide image, not a cover')
    img=ImageOps.exif_transpose(img).convert('RGB')
    img.thumbnail((650,850))
    return img


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dry-run',action='store_true')
    opts=parser.parse_args()
    html_path=ROOT/'index.html'
    html=html_path.read_text(encoding='utf8')
    match=re.search(r'(<script type="application/json" id="embedded-data" data-mode="published">)(.*?)(</script>)',html,re.S)
    if not match:raise SystemExit('Could not find embedded-data')
    state=json.loads(match.group(2))
    pubs_by_doi={p['doi'].lower():p for p in state['publications']}
    log=[]
    for ent in ENTRIES:
        doi=ent['doi'].lower();paper=pubs_by_doi.get(doi)
        if not paper:continue
        source=ent['url']
        if not source and ent['kind']=='issue' and ent.get('page'):
            source=discover_issue_cover(ent['page'],ent['journal'])
        if not source:
            log.append({'doi':doi,'status':'unavailable','reason':'No matched cover URL','source':ent['page']})
            continue
        file_name='paper-%02d.webp'%ent['number']
        path=ASSETS/file_name
        if opts.dry_run:
            log.append({'doi':doi,'status':'source-listed','url':source});continue
        try:
            im=fetch_image(source)
            im.save(path,'WEBP',quality=83,method=6)
            paper['image']='assets/covers/'+file_name
            paper['coverKind']=ent['kind']
            paper['coverSourceImage']=source
            log.append({'doi':doi,'status':'downloaded','file':str(path.relative_to(ROOT)),'url':source})
            print('Saved',file_name,ent['issue'])
        except Exception as exc:
            log.append({'doi':doi,'status':'failed','error':str(exc),'url':source})
            print('Skipped',ent['doi'],str(exc))
    if not opts.dry_run:
        json_data=json.dumps(state,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
        html=html[:match.start(2)]+json_data+html[match.end(2):]
        html_path.write_text(html,encoding='utf8')
    (ROOT/'cover-download-report.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    ok=sum(d['status']=='downloaded' for d in log)
    print(f'Downloaded {ok}/{len(ENTRIES)}; see cover-download-report.json for issue-by-issue status')

if __name__=='__main__':main()
