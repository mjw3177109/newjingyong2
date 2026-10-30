#!/usr/bin/env python3
"""Read-only SWF header and tag inventory. No protected art or source is redistributed."""
import argparse, collections, hashlib, json, struct, zlib
from pathlib import Path

TAG_NAMES={0:'End',1:'ShowFrame',2:'DefineShape',6:'DefineBits',9:'SetBackgroundColor',12:'DoAction',14:'DefineSound',15:'StartSound',18:'SoundStreamHead',20:'DefineBitsLossless',21:'DefineBitsJPEG2',22:'DefineShape2',26:'PlaceObject2',28:'RemoveObject2',32:'DefineShape3',34:'DefineButton2',35:'DefineBitsJPEG3',36:'DefineBitsLossless2',39:'DefineSprite',43:'FrameLabel',45:'SoundStreamHead2',46:'DefineMorphShape',48:'DefineFont2',56:'ExportAssets',59:'DoInitAction',69:'FileAttributes',72:'DoABC',76:'SymbolClass',82:'DoABC2',83:'DefineShape4',84:'DefineMorphShape2',87:'DefineBinaryData',90:'DefineBitsJPEG4'}

def read_swf(path):
    raw=Path(path).read_bytes()
    if len(raw)<9:raise ValueError('SWF too short')
    signature=raw[:3];version=raw[3];declared=struct.unpack_from('<I',raw,4)[0]
    if signature==b'FWS':data=raw
    elif signature==b'CWS':data=raw[:8]+zlib.decompress(raw[8:])
    elif signature==b'ZWS':raise ValueError('ZWS/LZMA SWF requires an LZMA-aware decoder such as FFDec')
    else:raise ValueError('not a SWF signature')
    if len(data)>300_000_000:raise ValueError('expanded SWF exceeds safety limit')
    nbits=data[8]>>3;rect_bytes=(5+4*nbits+7)//8;offset=8+rect_bytes
    if offset+4>len(data):raise ValueError('invalid frame header')
    fps_fixed=struct.unpack_from('<H',data,offset)[0];fps=fps_fixed/256
    frames=struct.unpack_from('<H',data,offset+2)[0];i=offset+4;counter=collections.Counter()
    while i<len(data):
        if i+2>len(data):raise ValueError('truncated tag header')
        short=struct.unpack_from('<H',data,i)[0];i+=2;tag,length=short>>6,short&63
        if length==63:
            if i+4>len(data):raise ValueError('truncated extended tag length')
            length=struct.unpack_from('<I',data,i)[0];i+=4
        if i+length>len(data):raise ValueError(f'tag {tag} exceeds file boundary')
        counter[f'{tag}:{TAG_NAMES.get(tag,"Other")}']+=1;i+=length
        if tag==0:break
    return {'file':Path(path).name,'sha256':hashlib.sha256(raw).hexdigest(), 'compressed_bytes':len(raw),'uncompressed_bytes':len(data),'declared_bytes':declared,'signature':signature.decode(),'swf_version':version,'fps':fps,'main_timeline_frames':frames,'tag_count':sum(counter.values()),'tag_counts':dict(sorted(counter.items(),key=lambda x:int(x[0].split(':')[0]))),'script_tag_hints':{'actionscript_1_2':counter['12:DoAction']+counter['59:DoInitAction'],'actionscript_3':counter['72:DoABC']+counter['82:DoABC2']},'note':'Tag counts are structural evidence, not recovered plot or gameplay equivalence.'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('swf');p.add_argument('--out');a=p.parse_args();r=read_swf(a.swf);report=json.dumps(r,indent=2,ensure_ascii=False);print(report)
 if a.out:
  dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(report+'\n',encoding='utf-8')
