# Mio Gusto ChatGPT ürün akışı

Ticimax XML (Google Merchant / Atom) akışını her saat OpenAI ürün akışı biçimine (CSV.GZ) çevirir ve GitHub Pages'te yayınlar.

- Betik: `convert.py`
- Zamanlama: `.github/workflows/feed.yml` (saatlik)
- Gizli bilgi: Ticimax XML adresi `XML_URL` adlı repository secret'ta durur, kodda yoktur.
- Yayın adresi: `https://miogusto.github.io/miogusto-chatgpt-feed/urunler.csv.gz`
- Güvenlik: 500'den az ürün çıkarsa yayın yapılmaz, önceki sürüm yayında kalır.
