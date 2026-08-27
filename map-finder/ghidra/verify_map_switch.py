# -*- coding: utf-8 -*-
"""Re-verify SOFT/RACE facts from bins. Offline. Does not patch.

    python map-finder/ghidra/verify_map_switch.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_interp_families import FLASH80, emulate_site, find_calls, HUBS  # noqa: E402
from trace_ram_writers import BIN, find_lea_abs  # noqa: E402
from trace_rail_to_end import dump_ann  # noqa: E402
from trace_rail_turbo_writers import lea_a0, movha_lea, sth_a0_bol, sth_bo_a0  # noqa: E402
from trace_a946_switch import classify_after_lea  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "reports" / "map-switch-verify.md"

NM_F, NM_OFF = 0.03125, -1024.0
APP_F = 0.09765625
RAIL_F = 0.0610359
A0 = 0xD0010800

CADDY_ORI = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules"
    r"\Caddy-CAYE-2013-03L906023PA-2531\ORI"
    r"\Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
)
CADDY_DIR = CADDY_ORI.parent.parent


def u16le(buf: bytes, off: int, n: int) -> list[int]:
    return list(struct.unpack_from("<%dH" % n, buf, off))


def nm(raw: int) -> float:
    return raw * NM_F + NM_OFF


def app_pct(raw: int) -> float:
    return raw * APP_F


def rail_bar(raw: int) -> float:
    return raw * RAIL_F


def max_nm_grid(buf: bytes, off: int, nbytes: int = 256) -> tuple[int, float]:
    vals = u16le(buf, off, nbytes // 2)
    mx = max(vals)
    return mx, nm(mx)


def max_rail(buf: bytes, off: int, nbytes: int = 512) -> tuple[int, float]:
    vals = u16le(buf, off, nbytes // 2)
    mx = max(vals)
    return mx, rail_bar(mx)


def ff_run(buf: bytes, off: int, n: int) -> int:
    chunk = buf[off : off + n]
    return sum(1 for b in chunk if b == 0xFF)


def zero_run(buf: bytes, off: int, n: int) -> int:
    chunk = buf[off : off + n]
    return sum(1 for b in chunk if b == 0)


def ptr_count(code: bytes, addr: int) -> int:
    pat = struct.pack("<I", addr)
    return code[:0x180000].count(pat)


def check(ok: bool) -> str:
    return "OK" if ok else "FAIL"


def main() -> None:
    code = BIN.read_bytes()
    lines: list[str] = []
    lines.append("# Vérif SOFT/RACE — 2026-08-23")
    lines.append("")
    lines.append("Relu **depuis les bins**, pas depuis la mémoire chat.")
    lines.append("Golf Ghidra : `%s`" % BIN)
    lines.append("")

    # --- AccPed hook ---
    emu = emulate_site(code, 0x800CC4AA)
    a4, a14, a15 = emu.A[4], emu.A[14], emu.A[15]
    lines.append("## 1) Hook AccPed (Golf 9980 fullflash)")
    lines.append("")
    lines.append("| Check | Résultat | Verdict |")
    lines.append("|-------|----------|---------|")
    lines.append(
        "| `800CC4AA` a4 | `%08X` | %s |"
        % (a4 or 0, check(a4 == 0xA01CFFC0))
    )
    lines.append(
        "| `800CC4AA` a14 APP | `%08X` | %s |"
        % (a14 or 0, check(a14 == 0xD0002198))
    )
    ax = (emu.A[5] or 0) & 0xFFFFFF
    ay = (emu.A[6] or 0) & 0xFFFFFF
    lines.append("| axe a5 (X) | `%06X` | lu |" % ax)
    lines.append("| axe a6 (Y) | `%06X` | lu |" % ay)

    xs = u16le(code, ax, 8)
    pcts = [round(app_pct(v), 1) for v in xs]
    lines.append("| points pédale raw | `%s` | |" % " ".join("%04X" % v for v in xs))
    lines.append("| points pédale %% | %s | 50 %% = col raw `0200` |" % pcts)
    has50 = 0x0200 in xs
    lines.append("| colonne 50 %% | %s | %s |" % (has50, check(has50)))

    raw_m, nm_m = max_nm_grid(code, 0x1CFFC0)
    lines.append(
        "| AccPed `1CFFC0` max | raw %d → **%.1f Nm** | Golf dump (pas Caddy V2) |"
        % (raw_m, nm_m)
    )
    lines.append("")

    # siblings
    lines.append("Sites AccPed a4 dans tuiles (re-emu) :")
    tiles = set()
    for t in (0x1CFFC0, 0x1CFAC0, 0x1CFBC0, 0x1CFCC0, 0x1CFDC0, 0x1CFEC0, 0x1D0640):
        tiles.add(0xA0000000 + t)
        tiles.add(0xA0000000 + t + 0x24)
    n_sites = 0
    for hub, info in HUBS.items():
        for va in find_calls(code, info["addr"]):
            e = emulate_site(code, va)
            if (e.A[4] or 0) in tiles:
                n_sites += 1
    lines.append("- count = **%d** (attendu 7)" % n_sites)
    lines.append("")

    # --- speed ---
    emu_s = emulate_site(code, 0x800A6B86)
    lines.append("## 2) Arrêt = `D0002810` ?")
    lines.append("")
    lines.append(
        "- site `tqlim_speed` intérieur `800A6B86` a14=`%08X` a13=`%08X` a4=`%08X`"
        % (emu_s.A[14] or 0, emu_s.A[13] or 0, emu_s.A[4] or 0)
    )
    ok2810 = (emu_s.A[14] or 0) == 0xD0002810
    okgrid = (emu_s.A[4] or 0) == 0xA01CEEF4
    lines.append("- a14 == `D0002810` : **%s**" % check(ok2810))
    lines.append("- a4 == intérieur `1CEEF4` (dans `tqlim_speed2A` `1CEED4`) : **%s**" % check(okgrid))
    lines.append("- atlas 9979 : axe X de cette map = *Vehicle speed* km/h (eByte `180CDB`)")
    lines.append("- **rôle** = vitesse véhicule. **Pas** un IdName OEM dans ce dump.")
    ax_s = (emu_s.A[5] or 0) & 0xFFFFFF
    lines.append("- axe X réel au call Golf : `%06X` (≠ atlas start `180CDB` — tile intérieure)" % ax_s)
    lines.append("")

    # --- A946 ---
    lines.append("## 3) `D000A946` n’est pas un switch")
    lines.append("")
    disp = (0xD000A946 - A0) & 0xFFFF
    a0s = lea_a0(code, disp)
    stb = sum(1 for va, ar in a0s if classify_after_lea(code, va - FLASH80, ar) == "st.b")
    ldb = sum(1 for va, ar in a0s if classify_after_lea(code, va - FLASH80, ar) == "ld.bu")
    lines.append("- lea [a0] : %d  ld.bu=%d  st.b=%d" % (len(a0s), ldb, stb))
    lines.append("- flash `19628D` = `0x%02X` (attendu 0x80)" % code[0x19628D])
    lines.append("")

    # --- holes ---
    lines.append("## 4) Trou RACE / cave / RAM")
    lines.append("")
    nff = ff_run(code, 0x1CB064, 3456)
    lines.append("- `1CB064` 3456 o FF : **%d/3456** %s" % (nff, check(nff == 3456)))
    nz = zero_run(code, 0x17FE04, 508)
    lines.append("- cave file `17FE04` (=VA `8017FE04`) zeros : **%d/508** %s" % (nz, check(nz == 508)))
    lines.append("- ptr code `8017FE04` : %d  `A017FE04` : %d" % (ptr_count(code, 0x8017FE04), ptr_count(code, 0xA017FE04)))
    lines.append("")
    lines.append("RAM `D0002890` (map_sel candidat) :")
    ram = 0xD0002890
    d = (ram - A0) & 0xFFFF
    clean = (
        len(find_lea_abs(code, ram)) == 0
        and len(lea_a0(code, d)) == 0
        and len(movha_lea(code, ram)) == 0
        and len(sth_a0_bol(code, d)) == 0
        and len(sth_bo_a0(code, d)) == 0
    )
    lines.append("- lea ABS / [a0] / movh / st.h BOL-BO : **%s**" % check(clean))
    lines.append("- **limite** : un accès par table/index n’apparaît pas dans ce scan.")
    lines.append("")

    # --- trampoline ---
    lines.append("## 5) Trampoline")
    lines.append("")
    call4 = code[0xCC4AA : 0xCC4AA + 4]
    lines.append("- octets `800CC4AA` : `%s` (call interp_2d attendu `6d …`)" % call4.hex(" "))
    lines.append("- **pas de cave code écrit**. Rien à flasher pour le switch.")
    lines.append("")

    # --- Caddy 9979 ---
    lines.append("## 6) Chiffres carto Caddy 9979 (atelier)")
    lines.append("")
    lines.append("Les 350 / 380 Nm, rail 1620 / 1656 viennent de **l’atlas 9979** (ORI vs ACE vs V2),")
    lines.append("pas du dump Golf Ghidra (AccPed Golf @`1CFFC0` = **%.1f Nm**)." % nm_m)
    lines.append("")
    if CADDY_ORI.is_file():
        caddy = CADDY_ORI.read_bytes()
        r, n = max_nm_grid(caddy, 0x1CF9C0)
        rr, rb = max_rail(caddy, 0x1E9368)
        lines.append("Caddy ORI relu : `%s`" % CADDY_ORI.name)
        lines.append("- AccPed `1CF9C0` max raw %d → **%.1f Nm** (atlas ori_max 293.7)" % (r, n))
        lines.append("- rail `1E9368` max raw %d → **%.1f bar** (atlas ori_max 1600)" % (rr, rb))
        # AccPed axis atlas 1A90C2
        xs_c = u16le(caddy, 0x1A90C2, 8)
        pct_c = [round(app_pct(v), 1) for v in xs_c]
        lines.append("- axe pédale `1A90C2` %% : %s  col 50%%=%s" % (pct_c, check(0x0200 in xs_c)))
    else:
        lines.append("Caddy ORI **absent** à ce chemin — stats atlas non re-mesurées ici.")
    lines.append("")
    # hunt ACE/V2 nearby
    found = []
    if CADDY_DIR.is_dir():
        for p in CADDY_DIR.rglob("*.bin"):
            name = p.name.lower()
            if any(k in name for k in ("ace", "v2", "v3", "italie", "stage")):
                found.append(p)
    if found:
        lines.append("Bins ACE/V2/V3 trouvés à côté :")
        for p in found[:12]:
            try:
                b = p.read_bytes()
            except OSError:
                continue
            if len(b) < 0x1E9568:
                continue
            ar, an = max_nm_grid(b, 0x1CF9C0)
            rr, rb = max_rail(b, 0x1E9368)
            lines.append("- `%s` AccPed **%.1f Nm**  rail **%.1f bar**" % (p.name, an, rb))
    else:
        lines.append("Pas de bin ACE/V2/V3 trouvé sous le dossier Caddy (stats atlas **non** re-lues sur fichier).")
    lines.append("")

    lines.append("## 7) Ce qu’on peut affirmer")
    lines.append("")
    lines.append("| Sujet | Confiance | Comment |")
    lines.append("|-------|-----------|---------|")
    lines.append("| AccPed Golf `1CFFC0` + APP `D0002198` + call `800CC4AA` | **haute** | emu + dump |")
    lines.append("| Colonne 50 % pédale | **haute** | axe Golf + atlas Caddy `0x0200` |")
    lines.append("| `D0002810` = vitesse (rôle) | **moyenne-haute** | X de tqlim_speed ; pas IdName |")
    lines.append("| Frein BLS | **aucune** | pas trouvé |")
    lines.append("| A946 ≠ switch maps | **haute** | cal `19628D` |")
    lines.append("| Trou FF `1CB064` / cave `8017FE04` | **haute** | scan octets |")
    lines.append("| RAM `D0002890` libre | **moyenne** | 0 xref classique, pas preuve absolue |")
    lines.append("| Rail 1620/1656, AccPed 350/380 | **atlas Caddy 9979** | pas le bin Golf ; ACE/V2 pas relus si fichiers absents |")
    lines.append("| Launch 2500 V3 | **atelier** (V3 vs V2 272 o clutch) | pas re-mesuré rpm dans cette passe |")
    lines.append("| Switch 3 coups dans l’ECU | **pas généré** | trampoline inexistant |")
    lines.append("")
    lines.append("**Ne pas flasher le Golf dump comme si c’était le Caddy.** AccPed n’est pas à la même adresse (`1CFFC0` vs `1CF9C0`).")
    lines.append("")

    text = "\n".join(lines) + "\n"
    # clean any empty oops
    OUT.write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(text)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
