"""
Exporte un assemblage Onshape en fichier STEP via l'API Translation.

Document cible : "mina engine" / élément "Assembly 1"
https://cad.onshape.com/documents/85087d6e52c312f630eb6b04/w/be04741c4c943f9329a9dece/e/a9592155383d4d160c356a35

Phases :
1. POST translation (génération STEP)
2. Polling jusqu'à DONE
3. Téléchargement vers mon_assemblage.step
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from onshape_client.client import Client
from onshape_client.oas.models.bt_translate_format_params import BTTranslateFormatParams

# Coordonnées de l'assemblage (depuis l'URL Onshape) — surchargeables via .env
DID = os.getenv("ONSHAPE_DID", "85087d6e52c312f630eb6b04")
WID = os.getenv("ONSHAPE_WID", "be04741c4c943f9329a9dece")
EID = os.getenv("ONSHAPE_EID", "a9592155383d4d160c356a35")

OUTPUT_FILE = Path(__file__).resolve().parent / "mon_assemblage.step"
POLL_INTERVAL_SEC = 2
POLL_TIMEOUT_SEC = 600


def make_client() -> Client:
    load_dotenv()
    Client.singleton_instance = None
    return Client(
        configuration={
            "base_url": os.getenv("ONSHAPE_BASE_URL"),
            "access_key": os.getenv("ONSHAPE_ACCESS_KEY"),
            "secret_key": os.getenv("ONSHAPE_SECRET_KEY"),
        },
        keys_file=None,
    )


def start_step_translation(client: Client):
    params = BTTranslateFormatParams(
        format_name="STEP",
        store_in_document=False,
        notify_user=False,
        destination_name="mon_assemblage",
    )
    print(f"Demande de traduction STEP… did={DID} wid={WID} eid={EID}")
    return client.assemblies_api.translate_format(DID, "w", WID, EID, params)


def wait_until_done(client: Client, translation_id: str):
    deadline = time.time() + POLL_TIMEOUT_SEC
    while time.time() < deadline:
        info = client.translation_api.get_translation(translation_id)
        state = info.request_state
        print(f"  Statut traduction : {state}")
        if state == "DONE":
            return info
        if state == "FAILED":
            raise RuntimeError(f"La traduction Onshape a échoué : {info.to_dict()}")
        time.sleep(POLL_INTERVAL_SEC)
    raise TimeoutError(
        f"Traduction toujours active après {POLL_TIMEOUT_SEC}s (id={translation_id})"
    )


def download_step(client: Client, external_data_id: str, dest: Path):
    print(f"Téléchargement du fichier STEP (fid={external_data_id})…")
    response = client.documents_api.download_external_data(
        DID,
        external_data_id,
        _preload_content=False,
    )
    data = response.data if hasattr(response, "data") else response
    if hasattr(data, "read"):
        data = data.read()
    dest.write_bytes(data)
    print(f"Fichier écrit : {dest} ({dest.stat().st_size} octets)")


def main():
    client = make_client()

    translation = start_step_translation(client)
    tid = translation.id
    print(f"Traduction créée : id={tid} état={translation.request_state}")

    done = wait_until_done(client, tid)
    result_ids = done.result_external_data_ids or []
    if not result_ids:
        raise RuntimeError(
            f"Traduction terminée sans fichier externe : {done.to_dict()}"
        )

    download_step(client, result_ids[0], OUTPUT_FILE)
    print("Export STEP terminé avec succès.")


if __name__ == "__main__":
    main()
