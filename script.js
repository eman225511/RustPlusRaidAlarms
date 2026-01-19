(function(){
  const defaultOwner = 'eman225511';
  const defaultRepo = 'RustPlusRaidAlarms';
  let repoOwner = defaultOwner;
  let repoName = defaultRepo;

  // Try to detect repo from any GitHub link on the page (more robust for forks/usernames)
  try {
    const anchors = Array.from(document.getElementsByTagName('a'));
    for (const a of anchors) {
      const m = a.href && a.href.match(/https?:\/\/github\.com\/([^\/]+)\/([^\/]+)(?:\/|$)/i);
      if (m) {
        repoOwner = m[1];
        repoName = m[2];
        break;
      }
    }
  } catch (e) {
    // ignore
  }

  const apiUrl = `https://api.github.com/repos/${repoOwner}/${repoName}/releases/latest`;

  const btn = document.getElementById('download-btn');
  const txt = document.getElementById('download-text');
  const btnHero = document.getElementById('download-btn-hero');
  const txtHero = document.getElementById('download-text-hero');
  const meta = document.getElementById('dl-meta');

  function setFallback() {
    btn.href = `https://github.com/${repoOwner}/${repoName}/releases/latest`;
    txt.textContent = 'View Releases';
    meta.textContent = 'Open releases page';
  }

  function chooseAsset(assets) {
    if (!assets || assets.length === 0) return null;
    // prefer zip files, then .tar.gz, else first asset
    const zip = assets.find(a => /\.zip$/i.test(a.name));
    if (zip) return zip;
    const tar = assets.find(a => /\.(tar|gz)$/i.test(a.name));
    if (tar) return tar;
    return assets[0];
  }

  function showSpinner() {
    meta.innerHTML = '<span class="spinner" aria-hidden="true"></span>Fetching latest...';
  }

  async function init() {
    if (!meta && !btn && !btnHero) return;
    showSpinner();
    try {
      const res = await fetch(apiUrl, { headers: { Accept: 'application/vnd.github.v3+json' } });
      if (!res.ok) {
        setFallback();
        meta.textContent = `Failed to fetch release (${res.status})`;
        return;
      }
      const data = await res.json();
      const asset = chooseAsset(data.assets);
      if (asset) {
        if (btn) { btn.href = asset.browser_download_url; btn.setAttribute('download', asset.name); }
        if (btnHero) { btnHero.href = asset.browser_download_url; btnHero.setAttribute('download', asset.name); }
        if (txt) txt.textContent = `Download ${asset.name}`;
        if (txtHero) txtHero.textContent = `Download ${asset.name}`;
        if (meta) meta.textContent = `Release: ${data.name || data.tag_name} • ${Math.round(asset.size/1024)} KB`;
      } else if (data.zipball_url) {
        // GitHub provides zipball for source
        if (btn) btn.href = data.zipball_url;
        if (btnHero) btnHero.href = data.zipball_url;
        if (txt) txt.textContent = `Download Source (zip)`;
        if (txtHero) txtHero.textContent = `Download Source (zip)`;
        if (meta) meta.textContent = `Release: ${data.name || data.tag_name}`;
      } else {
        setFallback();
      }
    } catch (err) {
      setFallback();
      if (meta) meta.textContent = 'Offline or blocked';
    }
  }

  init();
})();
