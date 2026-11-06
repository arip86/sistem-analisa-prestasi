from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

URL_COLUMNS: Tuple[str, ...] = (
    "url_peserta",
    "url_sertifikat",
    "url_foto_upp",
    "url_dokumen_undangan",
    "dosen_url_surat_tugas",
)
URL_PLACEHOLDER = "https://disamarkan.invalid"


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _split(value: Any) -> List[str]:
    text = _text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*;\s*", text) if part.strip()]


def _digest(salt: str, kind: str, value: str) -> str:
    return hmac.new(salt.encode("utf-8"), f"{kind}:{value}".encode("utf-8"), hashlib.sha256).hexdigest()


def _person_key(person_id: str, name: str) -> str:
    if person_id:
        return f"id:{person_id}"
    if name:
        return f"name:{name}"
    return ""


def _collect_keys(frame: pd.DataFrame, id_column: str, name_column: str) -> List[str]:
    keys = set()
    for _, row in frame.iterrows():
        ids = _split(row.get(id_column))
        names = _split(row.get(name_column))
        for index in range(max(len(ids), len(names))):
            person_id = ids[index] if index < len(ids) else ""
            name = names[index] if index < len(names) else ""
            key = _person_key(person_id, name)
            if key:
                keys.add(key)
    return sorted(keys, key=lambda key: _digest("", "person", key))


def _alias_identity(
    keys: Iterable[str],
    kind: str,
    label: str,
    salt: str,
    digits: int,
) -> Dict[str, Tuple[str, str]]:
    mapping: Dict[str, Tuple[str, str]] = {}
    used_ids = set()
    space = 10**digits
    aliases = sorted(keys, key=lambda key: _digest(salt, f"{kind}:order", key))
    for sequence, key in enumerate(aliases, start=1):
        digest = _digest(salt, f"{kind}:id", key)
        number = int(digest[:16], 16) % space
        alias_id = "9" + str(number).zfill(digits)
        while alias_id in used_ids:
            number = (number + 1) % space
            alias_id = "9" + str(number).zfill(digits)
        used_ids.add(alias_id)
        mapping[key] = (alias_id, f"{label} {sequence:03d}")
    return mapping


def _alias_url(value: Any, column: str, salt: str) -> Any:
    text = _text(value)
    if not text:
        return None if value is None else value
    token = _digest(salt, f"url:{column}", text)[:20]
    return f"{URL_PLACEHOLDER}/{column}/{token}"


def _anonymize_people(
    frame: pd.DataFrame,
    id_column: str,
    name_column: str,
    kind: str,
    label: str,
    salt: str,
    digits: int,
) -> None:
    keys = _collect_keys(frame, id_column, name_column)
    mapping = _alias_identity(keys, kind, label, salt, digits)
    ids_output: List[str] = []
    names_output: List[str] = []
    for _, row in frame.iterrows():
        ids = _split(row.get(id_column))
        names = _split(row.get(name_column))
        row_ids: List[str] = []
        row_names: List[str] = []
        for index in range(max(len(ids), len(names))):
            person_id = ids[index] if index < len(ids) else ""
            name = names[index] if index < len(names) else ""
            key = _person_key(person_id, name)
            if not key:
                continue
            alias_id, alias_name = mapping[key]
            row_ids.append(alias_id)
            row_names.append(alias_name)
        ids_output.append("; ".join(row_ids))
        names_output.append("; ".join(row_names))
    frame[id_column] = ids_output
    frame[name_column] = names_output


def anonymize_dataframe(frame: pd.DataFrame, salt: str) -> pd.DataFrame:
    salt = (salt or "").strip()
    if not salt:
        raise ValueError("ANONYMIZATION_SALT wajib diisi untuk data publik.")
    if frame.empty:
        return frame.copy()

    data = frame.copy()
    _anonymize_people(data, "mahasiswa_nim", "mahasiswa_nama", "mahasiswa", "Mahasiswa", salt, 9)
    _anonymize_people(data, "dosen_nuptk", "dosen_nama", "dosen", "Dosen", salt, 15)

    for column in URL_COLUMNS:
        if column in data.columns:
            data[column] = data[column].map(lambda value: _alias_url(value, column, salt))
    if "keterangan" in data.columns:
        data["keterangan"] = data["keterangan"].map(
            lambda value: "Disamarkan" if _text(value) else value
        )
    for column in ("fingerprint", "duplicate_group_key"):
        if column in data.columns:
            data[column] = None
    return data
