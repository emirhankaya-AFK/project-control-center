"""Safe, self-contained HTML report."""

from html import escape


def render_html(audit: dict) -> str:
    rows = []
    for repo in audit["repositories"]:
        name = escape(repo["name"])
        url = escape(repo["url"], quote=True)
        if not url.startswith("https://github.com/"):
            url = "#"
        status = "Özel" if repo["private"] else "Açık"
        if repo["archived"]:
            status += " · Arşiv"
        notes = ", ".join(repo["findings"]) or "Sorun işareti yok"
        rows.append(f"<tr><td><a href=\"{url}\">{name}</a></td><td>{escape(status)}</td>"
                    f"<td>{escape(repo['language'])}</td><td>{repo['score']}</td>"
                    f"<td>{escape(notes)}</td></tr>")
    overlaps = "".join(
        f"<li>{escape(d['a'])} ↔ {escape(d['b'])} ({d['similarity']:.0%})</li>"
        for d in audit["possible_name_overlaps"]
    ) or "<li>Belirgin isim benzerliği yok.</li>"
    return """<!doctype html><html lang="tr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Proje Kontrol Merkezi</title>
<style>body{font:16px system-ui;margin:0;background:#101827;color:#e7edf5}main{max-width:1200px;margin:auto;padding:32px}h1{font-size:2rem}a{color:#7bd5ff}table{width:100%;border-collapse:collapse;background:#192437}th,td{text-align:left;padding:10px;border-bottom:1px solid #304159}th{position:sticky;top:0;background:#24354d}section{overflow:auto} .stats{display:flex;gap:16px;flex-wrap:wrap}.stat{padding:16px;background:#24354d;border-radius:10px}input{padding:12px;width:min(100%,360px);background:#24354d;color:white;border:1px solid #557}</style>
<main><h1>Proje Kontrol Merkezi</h1>
<p>GitHub portföyü · Oluşturulma: """ + escape(audit["generated_at"]) + "</p>" + f"""
<div class="stats"><div class="stat">Toplam: {audit['total']}</div><div class="stat">Özel: {audit['private']}</div><div class="stat">Arşiv: {audit['archived']}</div></div>
<h2>Bakım sırası</h2><input id="search" aria-label="Proje ara" placeholder="Proje ara...">
<section><table id="repos"><thead><tr><th>Proje</th><th>Görünürlük</th><th>Dil</th><th>Puan</th><th>Bulgu</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></section>
<h2>Benzer isimler</h2><ul>""" + overlaps + """</ul>
<p>İsim benzerliği yalnızca inceleme önerisidir. Puan, kod kalitesi ölçümü değildir.</p></main>
<script>document.getElementById('search').addEventListener('input',e=>{let q=e.target.value.toLocaleLowerCase('tr');for(let r of document.querySelectorAll('#repos tbody tr'))r.hidden=!r.textContent.toLocaleLowerCase('tr').includes(q)})</script></html>"""

