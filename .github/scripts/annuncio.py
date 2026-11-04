"""Annuncia su Discord una release pubblicata, con il modello .github/annuncio-discord.md.

Le note sono quelle della release: si toglie tutto da "#### Screenshots" in poi, "### New" diventa "New" e
"- " diventa "• ". Una beta (pre-release) viene annunciata senza @here.
"""
import json
import os
import re
import urllib.request
from pathlib import Path

LIMITE_DISCORD = 2000


def note_discord(corpo):
    corpo = re.split(r"^#+\s*Screenshots\s*$", corpo, flags=re.M | re.I)[0]
    corpo = re.sub(r"<img[^>]*>", "", corpo)
    righe = []
    for riga in corpo.strip().splitlines():
        riga = re.sub(r"^#+\s*", "", riga.rstrip())
        riga = re.sub(r"^[-*]\s+", "• ", riga)
        righe.append(riga)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(righe)).strip()


def componi(modello, versione, link, note, beta):
    if beta:
        modello = modello.replace("@here ", "")
    testo = modello.replace("{versione}", versione).replace("{link}", link).strip()
    spazio = LIMITE_DISCORD - len(testo.replace("{note}", ""))
    if len(note) > spazio:  # Discord accetta al massimo 2000 caratteri: il resto è nella release
        note = note[: spazio - 2].rsplit("\n", 1)[0] + "\n…"
    return testo.replace("{note}", note)


def main():
    release = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))["release"]
    beta = release["prerelease"]
    testo = componi(
        Path(".github/annuncio-discord.md").read_text(encoding="utf-8"),
        release["tag_name"], release["html_url"], note_discord(release["body"] or ""), beta,
    )
    print(testo)
    dati = {"content": testo, "allowed_mentions": {"parse": [] if beta else ["everyone"]}}
    richiesta = urllib.request.Request(
        os.environ["DISCORD_WEBHOOK"], data=json.dumps(dati).encode(), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "DiscordBot (https://github.com/ASecretLibrary, 1)"},
    )
    with urllib.request.urlopen(richiesta) as risposta:
        print(f"Discord: {risposta.status}")


if __name__ == "__main__":
    main()
