# Engine modules recovery (PF-LRC-011)

Canonical archive on `main`: `SoundForge-Studio-Release-v2.18.zip`
(sha256 of archive: a0ceb7dcdf3629ba8e86f4c644f68ccb9ac7d8a11becdd7bc3d2e25ac2be56cd)

## Expected module identity (from archive)

| path | bytes | sha256 |
|------|------:|--------|
| app-core.js | 36957 | 36a2cb365c5aec48c133b7e7b90ab3dec1b9aa31d05805aa5662ac7bb3f47ab8 |
| app-ui.js | 34151 | e523340c4bf1a262e343859727cb62d135061325722ecfa5b5ebf44f5dcda3db |
| app-cinema.js | 8987 | 846f64bc74b75280f285699082f21671df93833767977567d0d7e850203f62ed |
| tools/studio_server.py | 11431 | 39c3c7c577b8eae53c65397298d9243682e27013fdae89909011c958581f6458 |
| tools/vocal_lab.py | 17510 | 2b7ddfc779eca371d584142a085c1463388965ffcdc6b0a79d30ceaa82c788fe |

To restore from the archive (byte-accurate):

```bash
unzip -o SoundForge-Studio-Release-v2.18.zip
python3 tools/restore_modules_from_zip.py
sha256sum app-core.js app-ui.js app-cinema.js tools/studio_server.py tools/vocal_lab.py
```

Checked-in module paths must match the table above for G1 PASS.
