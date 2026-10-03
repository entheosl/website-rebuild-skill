"""Preserve reference line work; the material upgrade must not redesign the image."""
from pathlib import Path
p=Path('demos/agent-runtime/index.html')
s=p.read_text()
if "artworkCleanup:'contour-preserving-median'" in s:
 print('Artwork cleanup already applied')
 raise SystemExit(0)
if "build:'mosaic-pbr-r3'" not in s:
 raise RuntimeError('PBR preparation must run first')
a=s.index(' // Clean interior colour, without magnifying')
b=s.index(' const position=',a)
s=s[:a]+s[b:]
s=s.replace(' let activeColor=[1,1,1],activeBounds=[0,0,1,1];',' let activeBounds=[0,0,1,1];')
s=s.replace('shade.push(activeColor[0]*tint,activeColor[1]*tint,activeColor[2]*tint);','shade.push(tint,tint,tint);')
s=s.replace('activeColor=tileColors[k];activeBounds=','activeBounds=')
needle=' const ceramic=new THREE.MeshPhysicalMaterial('
assert s.count(needle)==1
cleanup=''' // Mild impulse-noise removal only: retain all broad outlines and source colours.
 const cleanCanvas=document.createElement('canvas');cleanCanvas.width=cleanCanvas.height=N;
 const cleanContext=cleanCanvas.getContext('2d'),cleanPixels=cleanContext.createImageData(N,N);
 const samples=new Array(9);
 for(let y=0;y<N;y++)for(let x=0;x<N;x++){
  const i=(y*N+x)*4;
  for(let channel=0;channel<3;channel++){
   let n=0;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
    const yy=Math.max(0,Math.min(N-1,y+dy)),xx=Math.max(0,Math.min(N-1,x+dx));
    samples[n++]=rgba[(yy*N+xx)*4+channel];
   }
   samples.sort((a,b)=>a-b);cleanPixels.data[i+channel]=rgba[i+channel]*.35+samples[4]*.65;
  }
  cleanPixels.data[i+3]=255;
 }
 cleanContext.putImageData(cleanPixels,0,0);
 const glazeArtwork=new THREE.CanvasTexture(cleanCanvas);glazeArtwork.colorSpace=THREE.SRGBColorSpace;glazeArtwork.anisotropy=anisotropy;
'''
s=s.replace(needle,cleanup+needle)
s=s.replace('new THREE.MeshPhysicalMaterial({vertexColors:true,normalMap:ceramicNormal,normalScale:new THREE.Vector2(.5,.5)', 'new THREE.MeshPhysicalMaterial({map:glazeArtwork,vertexColors:true,normalMap:ceramicNormal,normalScale:new THREE.Vector2(.25,.25)')
s=s.replace('clearcoat:.65,clearcoatRoughness:.22','clearcoat:.8,clearcoatRoughness:.15,clearcoatNormalMap:ceramicNormal,clearcoatNormalScale:new THREE.Vector2(.10,.10)')
s=s.replace("build:'mosaic-pbr-r3',materials:","build:'mosaic-pbr-r3',artworkCleanup:'contour-preserving-median',materials:")
s=s.replace("loadtext.textContent='Loading PBR surfaces and studio lighting...';", "loadtext.textContent='\u6b63\u5728\u8f7d\u5165\u91c9\u9762\u3001\u7070\u6ce5\u3001\u6728\u7eb9\u4e0e\u6444\u5f71\u68da\u5149\u7167\u2026';")
p.write_text(s)
print('Retained source artwork and applied non-destructive ceramic cleanup')
