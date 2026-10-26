"""M043: sample-bound immutable lyric metadata; no ASR or singing claim."""
import array
import hashlib
import io
import json
import math
import sys
import wave


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def pcm_info(data):
    with wave.open(io.BytesIO(data), 'rb') as wav:
        if wav.getcomptype() != 'NONE' or wav.getsampwidth() != 2:
            raise ValueError('M043 supports PCM16 WAV only')
        rate, channels, frames = wav.getframerate(), wav.getnchannels(), wav.getnframes()
        if channels not in (1, 2) or not 8000 <= rate <= 192000 or not 0 < frames <= rate * 60:
            raise ValueError('bounded fixture required: 1-60 seconds, mono/stereo')
        pcm = wav.readframes(frames)
        if len(pcm) != frames * channels * 2: raise ValueError('truncated WAV')
    # Digest is decoded interleaved PCM16LE bytes; WAV container identity is separate.
    return {'sourceAudioDigest': hashlib.sha256(pcm).hexdigest(), 'sourceSampleRate': rate,
            'decodedFrameCount': frames, 'sourceChannels': channels, 'pcmEncoding': 's16le'}, pcm


def span(obj, count):
    a, b = obj['decodedSampleStart'], obj['decodedSampleEnd']
    if type(a) is not int or type(b) is not int or not 0 <= a < b <= count:
        raise ValueError('invalid sample range')
    return a, b


def validate(doc, audio, evidence):
    info, _ = pcm_info(audio)
    if any(doc.get(k) != v for k, v in info.items()): raise ValueError('decoded audio mismatch')
    count = info['decodedFrameCount']; outer = span(doc, count)
    if not isinstance(doc.get('alignmentModelOrMethod'), str) or not doc['alignmentModelOrMethod'].strip():
        raise ValueError('named alignment method required')
    if not isinstance(doc.get('language'), str) or not doc['language'].strip(): raise ValueError('language required')
    conf = doc['confidence']
    if conf is not None and (type(conf) not in (int, float) or not math.isfinite(conf) or not 0 <= conf <= 1):
        raise ValueError('invalid confidence')
    if doc.get('confidenceMeaning') != 'unknown; guided alignment is not recognition probability':
        raise ValueError('unsupported confidence semantics')
    if conf is not None: raise ValueError('this method does not estimate recognition confidence')
    if not isinstance(evidence, dict) or evidence.get('sourceAudioDigest') != info['sourceAudioDigest']:
        raise ValueError('evidence source mismatch')
    if doc.get('status') not in ('guided_candidate', 'corrected', 'unknown'): raise ValueError('invalid status')
    words, phrases = doc['words'], doc['phrases']
    if not isinstance(words, list) or not isinstance(phrases, list) or len(words) > 256 or len(phrases) > 256:
        raise ValueError('bounded lyric lists required')
    seen = {}; end = outer[0]
    for word in words:
        a, b = span(word, count)
        if a < end or b > outer[1]: raise ValueError('overlapping/outside words')
        if not isinstance(word.get('id'), str) or word['id'] in seen: raise ValueError('unique occurrence ID required')
        if not isinstance(word.get('text'), str) or not word['text'].strip() or len(word['text']) > 256:
            raise ValueError('nonempty word text required')
        seen[word['id']] = word; end = b
    used = []; end = outer[0]; phrase_ids = set()
    for phrase in phrases:
        a, b = span(phrase, count)
        if a < end or b > outer[1] or not phrase.get('wordIds'): raise ValueError('invalid phrase')
        if not isinstance(phrase.get('id'), str) or phrase['id'] in phrase_ids: raise ValueError('unique phrase ID required')
        phrase_ids.add(phrase['id']); end = b
        for wid in phrase['wordIds']:
            if wid not in seen or not a <= seen[wid]['decodedSampleStart'] < seen[wid]['decodedSampleEnd'] <= b:
                raise ValueError('phrase containment failure')
            used.append(wid)
    if used != [w['id'] for w in words]: raise ValueError('phrase membership/order mismatch')
    if doc['status'] == 'unknown' and (words or phrases): raise ValueError('unknown contains invented words')
    core = {k: v for k, v in doc.items() if k != 'revisionId'}
    if doc['revisionId'] != hashlib.sha256(canonical(core)).hexdigest(): raise ValueError('lyric identity mismatch')
    return doc


def islands(pcm, rate, channels):
    samples = array.array('h'); samples.frombytes(pcm)
    if sys.byteorder != 'little': samples.byteswap()
    hop = max(1, rate // 100)  # 10ms analysis blocks, never claimed phoneme exact.
    active = []
    for start in range(0, len(samples) // channels, hop):
        block = samples[start * channels:(start + hop) * channels]
        if block and max(abs(x) for x in block) >= 400: active.append(start)
    regions = []
    for start in active:
        if not regions or start - regions[-1][1] > rate // 8:
            regions.append([start, min(start + hop, len(samples) // channels)])
        else: regions[-1][1] = min(start + hop, len(samples) // channels)
    return regions


def candidate(audio, source_id, evidence_id, transcript, language='en'):
    info, pcm = pcm_info(audio)
    if not isinstance(transcript, str) or len(transcript) > 4096: raise ValueError('bounded known transcript required')
    tokens = transcript.split(); regions = islands(pcm, info['sourceSampleRate'], info['sourceChannels'])
    # Deliberately conservative: align only supplied words to separated vocal islands.
    # No recognition, no voice detection and no inference that energy means singing.
    matched = bool(tokens) and len(tokens) == len(regions) and len(tokens) <= 256
    words = [{'id': f'w{i}', 'text': text, 'decodedSampleStart': a, 'decodedSampleEnd': b}
             for i, (text, (a, b)) in enumerate(zip(tokens, regions))] if matched else []
    core = {**info, 'formatVersion': 1, 'sourceArtifactId': source_id, 'parentRevisionId': None,
            'parentArtifactId': None, 'language': language, 'alignmentModelOrMethod': 'known-text-energy-islands-v1',
            'evidenceArtifactId': evidence_id, 'decodedSampleStart': 0, 'decodedSampleEnd': info['decodedFrameCount'],
            'confidence': None, 'confidenceMeaning': 'unknown; guided alignment is not recognition probability',
            'status': 'guided_candidate' if matched else 'unknown', 'words': words,
            'phrases': [{'id': 'p0', 'wordIds': [w['id'] for w in words],
                         'decodedSampleStart': words[0]['decodedSampleStart'], 'decodedSampleEnd': words[-1]['decodedSampleEnd']}] if words else [],
            'correctionHistory': []}
    return {'revisionId': hashlib.sha256(canonical(core)).hexdigest(), **core}


def correction(parent, parent_artifact, changes, actor, reason):
    if not isinstance(actor, str) or not actor.strip() or len(actor) > 128: raise ValueError('correction actor required')
    if not isinstance(reason, str) or len(reason) > 1024: raise ValueError('invalid reason')
    if not isinstance(changes, list) or not 0 < len(changes) <= 256: raise ValueError('changes required')
    doc = json.loads(json.dumps(parent)); words = {w['id']: w for w in doc['words']}; delta = []; ids = set()
    for change in changes:
        wid = change['wordId']; text = change['text']
        if wid in ids or wid not in words or not isinstance(text, str) or not text.strip() or len(text) > 256:
            raise ValueError('invalid corrected occurrence')
        ids.add(wid); old = words[wid]['text']
        if old == text: raise ValueError('no-op correction')
        words[wid]['text'] = text
        delta.append({'wordId': wid, 'before': old, 'after': text})
    doc.update(parentRevisionId=parent['revisionId'], parentArtifactId=parent_artifact, status='corrected')
    doc['correctionHistory'].append({'actor': actor, 'reason': reason, 'changes': delta,
                                      'parentRevisionId': parent['revisionId']})
    doc.pop('revisionId'); return {'revisionId': hashlib.sha256(canonical(doc)).hexdigest(), **doc}
