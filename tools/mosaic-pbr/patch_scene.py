"""Apply scoped, assertion-checked scene changes; never rewrite unrelated repository files."""
from pathlib import Path
import hashlib

p=Path('demos/agent-runtime/index.html')
original=p.read_text()
if "build:'mosaic-pbr-r3'" in original:
 print('PBR scene is already installed')
 raise SystemExit(0)
raw=p.read_bytes()
blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
if blob!='89c4c62b433893f5faf7402456d071cf92272e8c':
 raise RuntimeError('Scene changed since inspection; refusing to overwrite: '+blob)
def change(old,new):
 global original
 if original.count(old)!=1:
  raise RuntimeError('Expected one match: '+old[:120])
 original=original.replace(old,new)
change('TESSERAE / THREE.JS','TESSERAE / PBR GLAZE')
change(" const position=[],normal=[],uv=[],shade=[],centers=[],motions=[],tiles=[];",''' // Clean interior colour, without magnifying the video's compressed surface/noise.
 const cellPixels=Array.from({length:seeds.length},()=>[]);
 for(let i=0;i<total;i++){const k=labels[i]-1;if(k>=0&&dist[i]>.9)cellPixels[k].push(i);}
 const tileColors=cellPixels.map((pixels,k)=>{
  if(!pixels.length)pixels=[seeds[k]];
  pixels.sort((a,b)=>gray[a]-gray[b]);
  const lo=Math.floor(pixels.length*.30),hi=Math.max(lo+1,Math.ceil(pixels.length*.85));
  let r=0,g=0,b=0;for(let i=lo;i<hi;i++){const j=pixels[i]*4;r+=rgba[j];g+=rgba[j+1];b+=rgba[j+2];}
  const n=(hi-lo)*255,c=new THREE.Color().setRGB(r/n,g/n,b/n,THREE.SRGBColorSpace);
  return[c.r,c.g,c.b];
 });
 const position=[],normal=[],uv=[],surfaceUV=[],shade=[],centers=[],motions=[],tiles=[];
 let activeColor=[1,1,1],activeBounds=[0,0,1,1];''')
change('shade.push(tint,tint,tint);','shade.push(activeColor[0]*tint,activeColor[1]*tint,activeColor[2]*tint);surfaceUV.push((p[0]-activeBounds[0])/activeBounds[2],1-(p[2]-activeBounds[1])/activeBounds[3]);')
change('  const s=random(k),s2=random(k+534),s3=random(k+1753),height=.047+s*.027,','''  const minX=Math.min(...p.map(v=>v[0])),maxX=Math.max(...p.map(v=>v[0])),minY=Math.min(...p.map(v=>v[1])),maxY=Math.max(...p.map(v=>v[1]));
  activeColor=tileColors[k];activeBounds=[(minX/N-.5)*10,(minY/N-.5)*10,Math.max(.001,(maxX-minX)/N*10),Math.max(.001,(maxY-minY)/N*10)];
  const s=random(k),s2=random(k+534),s3=random(k+1753),height=.047+s*.012,''')
change('height-.012','height-.009')
change('(v[0]/N*10-5-center[0])*.92,height,center[2]+(v[1]/N*10-5-center[2])*.92','(v[0]/N*10-5-center[0])*.96,height,center[2]+(v[1]/N*10-5-center[2])*.96')
change('renderer.toneMappingExposure=.65','renderer.toneMappingExposure=.85')
change("const scene=new THREE.Scene();scene.background=new THREE.Color('#9a8770');scene.fog=new THREE.Fog('#9a8770',30,75);", "const scene=new THREE.Scene();scene.background=new THREE.Color('#b9ae9b');scene.fog=new THREE.Fog('#b9ae9b',30,75);")
change("scene.add(new THREE.HemisphereLight('#fff9ef','#595147',1.1));", "scene.add(new THREE.HemisphereLight('#fffaf3','#7d766b',.40));")
change("new THREE.DirectionalLight('#fff9ed',2.6)","new THREE.DirectionalLight('#fff9ed',1.65)")
change('sun.shadow.mapSize.set(innerWidth<900?1024:2048,innerWidth<900?1024:2048)','sun.shadow.mapSize.set(2048,2048)')
begin=original.index(' // Plaster substrate')
end=original.index(' // Thin etched underdrawing',begin)
change(original[begin:end],''' // Official CC0 ceramic/plaster/wood PBR data; all assets are on this same origin.
 loadtext.textContent='Loading PBR surfaces and studio lighting...';
 const loader=new THREE.TextureLoader(),assetURL=new URL('./assets/pbr/',import.meta.url);
 const anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy()),loadedPBR=[];
 async function readMap(name,color=false,repeat=[1,1]){
  let timer;
  const t=await Promise.race([loader.loadAsync(new URL(name,assetURL).href),new Promise((_,reject)=>timer=setTimeout(()=>reject(Error('PBR texture timeout: '+name)),30000))]).finally(()=>clearTimeout(timer));
  t.colorSpace=color?THREE.SRGBColorSpace:THREE.NoColorSpace;
  t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(...repeat);t.anisotropy=anisotropy;
  loadedPBR.push({file:name,width:t.image.width,height:t.image.height});return t;
 }
 const [ceramicNormal,ceramicRough,plasterColor,plasterNormal,plasterRough,woodColor,woodNormal,woodRough]=await Promise.all([
  readMap('ceramic-normal.webp'),readMap('ceramic-roughness.webp'),
  readMap('plaster-color.webp',true,[3,3]),readMap('plaster-normal.webp',false,[3,3]),readMap('plaster-roughness.webp',false,[3,3]),
  readMap('wood-color.webp',true),readMap('wood-normal.webp'),readMap('wood-roughness.webp')
 ]);
 ceramicNormal.channel=ceramicRough.channel=1;
 const {RGBELoader}=await import('./vendor/RGBELoader.js');
 const hdr=await new RGBELoader().loadAsync(new URL('studio-small-09.hdr',assetURL).href);
 const pmrem=new THREE.PMREMGenerator(renderer);pmrem.compileEquirectangularShader();
 const studio=pmrem.fromEquirectangular(hdr);scene.environment=studio.texture;
 scene.environmentIntensity=.65;scene.environmentRotation.y=.65;hdr.dispose();pmrem.dispose();
 const baseMat=new THREE.MeshStandardMaterial({map:plasterColor,normalMap:plasterNormal,normalScale:new THREE.Vector2(.25,.25),roughnessMap:plasterRough,roughness:1,color:'#fff9ec'});
 const board=new THREE.Mesh(new THREE.BoxGeometry(10.5,.22,10.5),baseMat);board.position.y=-.11;board.receiveShadow=true;scene.add(board);
 const floorMat=baseMat.clone();floorMat.color.set('#d3cabb');floorMat.normalScale.set(.15,.15);
 for(const key of ['map','normalMap','roughnessMap']){floorMat[key]=baseMat[key].clone();floorMat[key].repeat.set(32,32);floorMat[key].needsUpdate=true;}
 const floor=new THREE.Mesh(new THREE.PlaneGeometry(160,160),floorMat);floor.rotation.x=-Math.PI/2;floor.position.y=-.34;floor.receiveShadow=true;scene.add(floor);
 const wood=new THREE.MeshPhysicalMaterial({map:woodColor,normalMap:woodNormal,normalScale:new THREE.Vector2(.35,.35),roughnessMap:woodRough,roughness:1,metalness:0,clearcoat:.20,clearcoatRoughness:.35});
 // UVs align the timber grain along the separate frame rails.
 for(let i=0;i<4;i++){
  const railGeo=new THREE.BoxGeometry(.16,.25,10.84),a=railGeo.attributes.uv;
  for(let j=0;j<a.count;j++)a.setXY(j,a.getX(j)*.13+(i*.21)%1,a.getY(j)*2.4);a.needsUpdate=true;
  const m=new THREE.Mesh(railGeo,wood);if(i<2)m.rotation.y=Math.PI/2;
  m.position.set(i<2?0:(i===2?-5.34:5.34),-.045,i<2?(i===0?-5.34:5.34):0);m.castShadow=m.receiveShadow=true;scene.add(m);
 }
''')
change("geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));", "geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geo.setAttribute('uv1',new THREE.Float32BufferAttribute(surfaceUV,2));")
change('new THREE.MeshStandardMaterial({map:texture,vertexColors:true,roughness:.83,metalness:0,bumpMap:sandMap,bumpScale:.004})','new THREE.MeshPhysicalMaterial({vertexColors:true,normalMap:ceramicNormal,normalScale:new THREE.Vector2(.5,.5),roughnessMap:ceramicRough,roughness:1,metalness:0,ior:1.48,clearcoat:.65,clearcoatRoughness:.22,envMapIntensity:1.1})')
change("build:'mosaic-three-r2',ready", "build:'mosaic-pbr-r3',materials:{type:ceramic.type,clearcoat:ceramic.clearcoat,roughness:ceramic.roughness,normalScale:ceramic.normalScale.x,environment:Boolean(scene.environment),maps:loadedPBR},ready")
change('<title>陶片成画 · Three.js</title>', '<title>陶片成画 · PBR 釉面</title>')
p.write_text(original)
print('Patched scene:', len(original), 'characters')
