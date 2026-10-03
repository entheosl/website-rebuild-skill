"""Download verified CC0 sources and bake mobile-friendly material maps."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import hashlib
import io
import json
import numpy as np
import urllib.request
import zipfile

ROOT = Path.cwd()
RAW = Path('/tmp/mosaic-pbr-raw')
OUT = ROOT / 'demos/agent-runtime/assets/pbr'
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = [
 ('Tiles107_4K-JPG.zip', 'https://ambientcg.com/get?file=Tiles107_4K-JPG.zip', 'd33eb396c7529b30bc50a16d8f69800297681a053582f1aa4681ecdd700ea0e0', 'https://ambientcg.com/view?id=Tiles107'),
 ('beige_wall_001_diff.jpg', 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/beige_wall_001/beige_wall_001_diff_2k.jpg', '222d4d2e7d5c425c97e5a66790852388cec7706714d773f769fba6bfe08cea4e', 'https://polyhaven.com/a/beige_wall_001'),
 ('beige_wall_001_nor_gl.jpg', 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/beige_wall_001/beige_wall_001_nor_gl_2k.jpg', '7f5cbecd6766f44034f3b78b4addb1559e12bdd5a77501bd418a736609e7cedc', 'https://polyhaven.com/a/beige_wall_001'),
 ('beige_wall_001_rough.jpg', 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/beige_wall_001/beige_wall_001_rough_2k.jpg', 'a76e2307d8ec47d1be1d4710851fc4545db7aecfa176333738a6756358b64767', 'https://polyhaven.com/a/beige_wall_001'),
 ('wood_table_001_diff.jpg', 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/wood_table_001/wood_table_001_diff_2k.jpg', '63ae5cd186197b40f18bc020fe2b652bb08df4d9fc6240c6cbf8a7e3bc32c096', 'https://polyhaven.com/a/wood_table_001'),
 ('wood_table_001_nor_gl.jpg', 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/wood_table_001/wood_table_001_nor_gl_2k.jpg', 'd56f02c911391267ddc6adc92e8a5bc29b9803196e8d57ad5b9702e6c842dc28', 'https://polyhaven.com/a/wood_table_001'),
 ('wood_table_001_rough.jpg', 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/wood_table_001/wood_table_001_rough_2k.jpg', 'c788876d80e4d96598590631f8de92447fb1b0ba1265a812514ee717d270ac3e', 'https://polyhaven.com/a/wood_table_001'),
 ('studio_small_09_1k.hdr', 'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_09_1k.hdr', 'e7cfda5f4e98e623db12b8bfd0184e048488e4855d9c83e2751fb44a32e80c45', 'https://polyhaven.com/a/studio_small_09'),
]

def download(source):
 name, url, expected, page = source
 path = RAW / name
 if not path.exists():
  request = urllib.request.Request(url, headers={'User-Agent': 'MosaicMaterialBuild/1.0'})
  with urllib.request.urlopen(request, timeout=90) as response:
   path.write_bytes(response.read())
 data = path.read_bytes()
 actual = hashlib.sha256(data).hexdigest()
 if actual != expected:
  raise RuntimeError(f'Source checksum changed: {name}: {actual}')
 print('Verified', name, len(data), flush=True)
 return {'file': name, 'url': url, 'source': page, 'license': 'CC0-1.0', 'bytes': len(data), 'sha256': actual}

with ThreadPoolExecutor(max_workers=3) as executor:
 provenance = list(executor.map(download, SOURCES))
with zipfile.ZipFile(RAW/'Tiles107_4K-JPG.zip') as archive:
 for name in archive.namelist():
  if name.endswith(('_NormalGL.jpg', '_Roughness.jpg')):
   (RAW/Path(name).name).write_bytes(archive.read(name))

# Extract the ceramic face, not its surrounding tile grid / grout.
box = (1056, 1056, 1504, 1504)
Image.open(RAW/'Tiles107_4K-JPG_NormalGL.jpg').convert('RGB').crop(box).save(OUT/'ceramic-normal.webp', lossless=True, method=6)
a = np.asarray(Image.open(RAW/'Tiles107_4K-JPG_Roughness.jpg').convert('L').crop(box), dtype=np.float32)/255
# Satin glaze, instead of either sandpaper or a perfect mirror.
a = np.clip(.285 + .65*a, .285, .44)
Image.fromarray(np.uint8(a*255)).convert('RGB').save(OUT/'ceramic-roughness.webp', lossless=True, method=6)
for name, stem, size in [('plaster', 'beige_wall_001', 2048), ('wood', 'wood_table_001', 1024)]:
 for kind, suffix in [('color', 'diff'), ('normal', 'nor_gl'), ('roughness', 'rough')]:
  image = Image.open(RAW/(stem+'_'+suffix+'.jpg')).convert('RGB')
  target = size if kind == 'color' else 1024
  image = image.resize((target, target), Image.Resampling.LANCZOS)
  if kind == 'roughness':
   a = np.asarray(image, dtype=np.float32)/255
   a = (.75+.22*a) if name == 'plaster' else (.36+.42*a)
   image = Image.fromarray(np.uint8(np.clip(a, 0, 1)*255))
  image.save(OUT/(name+'-'+kind+'.webp'), quality=90 if kind == 'color' else 96, method=6)
(OUT/'studio-small-09.hdr').write_bytes((RAW/'studio_small_09_1k.hdr').read_bytes())
manifest = {'version': 'pbr-r3', 'sources': provenance, 'assets': []}
for path in sorted(OUT.iterdir()):
 if path.suffix not in ['.webp', '.hdr']:
  continue
 entry = {'file': path.name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
 if path.suffix == '.webp':
  entry['dimensions'] = list(Image.open(path).size)
 manifest['assets'].append(entry)
manifest['downloadBytes'] = sum(a['bytes'] for a in manifest['assets'])
if manifest['downloadBytes'] > 3500000:
 raise RuntimeError('Material download budget exceeded')
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2))
(OUT/'LICENSES.md').write_text('''# Material provenance

These materials are CC0-1.0. The scene keeps the reference artwork colours; the online ceramic asset supplies surface normals and roughness, not a replacement picture.

- Ceramic: ambientCG Tiles 107, https://ambientcg.com/view?id=Tiles107 . One grout-free face is cropped from the 4K source and its roughness is remapped for satin glaze.
- Plaster: Poly Haven Beige Wall 001, https://polyhaven.com/a/beige_wall_001 . 2K colour and 1K normal/roughness WebP maps.
- Wood: Poly Haven Wood Table 001, https://polyhaven.com/a/wood_table_001 . 1K colour/normal/roughness WebP maps.
- Lighting: Poly Haven Studio Small 09, https://polyhaven.com/a/studio_small_09 . 1K Radiance HDR, prefiltered at runtime with PMREM.
- License documentation: https://docs.ambientcg.com/license/ and https://polyhaven.com/license

`manifest.json` records the downloaded URLs, checksums, derivatives and sizes. Do not interpret a 4K source atlas as a 4K resolution individual ceramic face.
''')
print('Material download bytes:', manifest['downloadBytes'])
