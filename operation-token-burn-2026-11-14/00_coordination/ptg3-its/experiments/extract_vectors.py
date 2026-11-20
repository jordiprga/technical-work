"""Extract four NIST COUNT=0 traces from the public CAVP archive (offline)."""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

URL = 'https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/drbg/drbgtestvectors.zip'
ZIP_SHA = '5f7e5658ebd5b4e6785a7b12fa32333511d2acc2f2d9c5ae1ffa16b699377769'


def extract(archive):
    raw = Path(archive).read_bytes()
    if sha256(raw).hexdigest() != ZIP_SHA:
        raise ValueError('Unexpected CAVP archive SHA-256')
    vectors = []
    with ZipFile(BytesIO(raw)) as outer:
        for category in ['no_reseed', 'pr_false']:
            member = f'drbgvectors_{category}.zip'
            with ZipFile(BytesIO(outer.read(member))) as inner:
                payload = inner.read('CTR_DRBG.txt')
            sections = payload.decode('ascii').split('[AES-256 no df]')[1:]
            for additional_len in [0, 384]:
                header = (f'[PersonalizationStringLen = 0]\n[AdditionalInputLen = {additional_len}]\n'
                          '[ReturnedBitsLen = 512]')
                section = next(s for item in sections if header in (s := item.replace('\r\n', '\n')).split('COUNT = 0')[0])
                trace = section.split('COUNT = 0\n', 1)[1].split('COUNT = 1\n', 1)[0]
                def field(name):
                    return re.findall('^' + name + r' = ([0-9a-f]*)$', trace, re.M)
                states = {}
                for label, key, v in re.findall(r'^\*\* ([^:]+):\n\s+Key = ([0-9a-f]+)\n\s+V\s+= ([0-9a-f]+)', trace, re.M):
                    states[label] = [key, v]
                vectors.append(dict(member=member, trace_file='CTR_DRBG.txt', trace_file_sha256=sha256(payload).hexdigest(),
                                    count=0, additional_input_len=additional_len, returned_bits_len=512,
                                    entropy=field('EntropyInput')[0], reseed_entropy=next(iter(field('EntropyInputReseed')), None),
                                    reseed_additional=next(iter(field('AdditionalInputReseed')), None),
                                    additional=field('AdditionalInput'), second_output=field('ReturnedBits')[0], states=states))
    return dict(source=URL, zip_sha256=ZIP_SHA, accessed='2026-11-20', mode='AES-256 no df', vectors=vectors)


if __name__ == '__main__':
    print(json.dumps(extract(sys.argv[1]), indent=2))
