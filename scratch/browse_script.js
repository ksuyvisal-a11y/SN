
(function(){
  var API="https://explorer.hongguodownloader.com";
  var DL="https://github.com/M4St3r0/hongguo-downloader/releases/latest/download/HongguoDownloader-Setup.exe";
  var CAT_SIZE=48, LB_SIZE=100, FAV_KEY="hg-browse-favs";
  var $=function(s){return document.querySelector(s);};
  function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function fmt(n){ try{ return (n||0).toLocaleString(); }catch(e){ return ''+(n||0); } }
  var mode="leaderboard", cat="all", genre="", q="", sort="newest", status="", page=1, seq=0, genresLoaded=false, itemsById={};

  var toastT; function toast(msg){ var el=$('#bzToast'); if(!el) return; el.textContent=msg; el.classList.add('show'); clearTimeout(toastT); toastT=setTimeout(function(){ el.classList.remove('show'); }, 1700); }
  function copy(text, msg){
    function ok(){ toast(msg); }
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(text).then(ok).catch(fb); } else fb();
    function fb(){ try{ var ta=document.createElement('textarea'); ta.value=text; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); ok(); }catch(e){ toast('Copy failed'); } }
  }

  // favorites (per-browser, localStorage)
  function loadFavs(){ try{ return JSON.parse(localStorage.getItem(FAV_KEY)||'{}')||{}; }catch(e){ return {}; } }
  function saveFavs(){ try{ localStorage.setItem(FAV_KEY, JSON.stringify(favs)); }catch(e){} }
  var favs=loadFavs();
  function favCount(){ return Object.keys(favs).length; }
  function renderFavUI(){
    var n=$('#bzSavedN'); if(n) n.textContent=favCount();
    document.querySelectorAll('#lbGrid .bz-card').forEach(function(c){ var b=c.querySelector('.bz-fav'); if(b) b.classList.toggle('on', !!favs[c.dataset.id]); });
  }
  function toggleFav(id){
    if(favs[id]){ delete favs[id]; toast('Removed from saved'); }
    else { var x=itemsById[id]; if(!x) return; favs[id]={id:id,t:x.title||'',c:x.cover||'',e:x.episode_cnt||'',s:x.score||''}; toast('Saved ♥'); }
    saveFavs(); renderFavUI();
  }

  function card(x, rank){
    var t=esc(x.title||''), id=esc(String(x.series_id||''));
    return '<div class="bz-card" data-id="'+id+'">'
      +'<div class="lb-art" role="button" tabindex="0" aria-label="'+t+' — details">'
        +(rank?'<span class="lb-rank'+(rank<=3?' top':'')+'">'+rank+'</span>':'')
        +(x.score?'<span class="lb-score">★ '+esc(x.score)+'</span>':'')
        +'<img src="'+esc(x.cover||'')+'" loading="lazy" alt="'+t+'" onerror="this.style.visibility=\'hidden\'">'
        +((x.episode_cnt||x.heat)?('<span class="lb-eps">'+(x.episode_cnt?(x.episode_cnt+' eps'):('🔥 '+esc(x.heat)))+'</span>'):'')
        +(x.status==='completed'?'<span class="lb-status">✓ Done</span>':(x.status==='ongoing'?'<span class="lb-status">● Ongoing</span>':''))
      +'</div>'
      +'<div class="lb-ttl">'+t+'</div>'
      +'<div class="bz-actions">'
        +'<button class="bz-fav" type="button" data-fav title="Save to your list" aria-label="Save">♥</button>'
        +'<button class="bz-cp" type="button" data-cp="title" title="Copy the title">⧉ Title</button>'
        +'<button class="bz-cp" type="button" data-cp="link" title="Copy a 《》 tag to paste into the app">《》</button>'
      +'</div></div>';
  }
  function skeleton(n){ var s=''; for(var i=0;i<n;i++) s+='<div class="bz-sk"></div>'; return s; }

  function buildPager(cur, pages){
    var el=$('#lbPager'); if(!el) return;
    if(mode!=='catalog' || pages<=1){ el.hidden=true; el.innerHTML=''; return; }
    el.hidden=false;
    var nums=[1], lo=Math.max(2,cur-2), hi=Math.min(pages-1,cur+2);
    if(lo>2) nums.push('…');
    for(var p=lo;p<=hi;p++) nums.push(p);
    if(hi<pages-1) nums.push('…');
    if(pages>1) nums.push(pages);
    el.innerHTML='<button class="bz-pg" data-pg="'+(cur-1)+'"'+(cur<=1?' disabled':'')+'>‹ Prev</button>'
      +nums.map(function(p){ return p==='…' ? '<span class="bz-gap">…</span>' : '<button class="bz-pg'+(p===cur?' on':'')+'" data-pg="'+p+'">'+p+'</button>'; }).join('')
      +'<button class="bz-pg" data-pg="'+(cur+1)+'"'+(cur>=pages?' disabled':'')+'>Next ›</button>';
    el.querySelectorAll('.bz-pg[data-pg]').forEach(function(b){ b.onclick=function(){ var p=parseInt(b.dataset.pg,10); if(!b.disabled && p>=1){ page=p; load(true); } }; });
  }

  // shareable URL state
  function syncURL(){
    var p=new URLSearchParams();
    p.set('tab', mode);
    if(mode==='leaderboard'){ if(cat!=='all') p.set('cat',cat); }
    else { if(genre) p.set('genre',genre); if(q) p.set('q',q); if(sort!=='newest') p.set('sort',sort); if(status) p.set('status',status); if(page>1) p.set('page',page); }
    var qs=p.toString();
    try{ history.replaceState(null,'', qs?('?'+qs):location.pathname); }catch(e){}
  }
  function initFromURL(){
    var p; try{ p=new URLSearchParams(location.search); }catch(e){ return; }
    var t=p.get('tab'); if(t==='catalog'||t==='leaderboard') mode=t;
    if(mode==='leaderboard'){ var c=p.get('cat'); if(['all','human','comic','ai'].indexOf(c)>=0) cat=c; }
    else {
      genre=p.get('genre')||''; q=p.get('q')||'';
      var so=p.get('sort'); if(['popular','newest','eps'].indexOf(so)>=0) sort=so;
      var st=p.get('status'); if(['completed','ongoing'].indexOf(st)>=0) status=st;
      page=Math.max(1, parseInt(p.get('page')||'1',10)||1);
    }
  }

  function load(scroll){
    var my=++seq, grid=$('#lbGrid'); if(!grid) return;
    grid.innerHTML=skeleton(mode==='leaderboard'?24:18);
    var url = mode==='leaderboard'
      ? API+'/leaderboard?board=hot&category='+encodeURIComponent(cat)+'&size='+LB_SIZE
      : API+'/explorer?page='+page+'&size='+CAT_SIZE+'&sort='+encodeURIComponent(sort)+(status?'&status='+encodeURIComponent(status):'')+(genre?'&genre='+encodeURIComponent(genre):'')+(q?'&q='+encodeURIComponent(q):'');
    fetch(url).then(function(r){return r.json();}).then(function(d){
      if(my!==seq) return;
      var items=d.items||[];
      items.forEach(function(x){ itemsById[String(x.series_id)]=x; });
      if(!items.length){ grid.innerHTML='<div class="lb-empty">'+(d&&d.error?'The live catalogue is briefly over its data limit — please try again in a little while.':'Nothing matches that — try another genre or search.')+'</div>'; $('#lbCount').textContent=''; buildPager(1,1); syncURL(); return; }
      grid.innerHTML=items.map(function(x,i){ return card(x, mode==='leaderboard'?i+1:0); }).join('');
      renderFavUI();
      if(mode==='leaderboard'){
        $('#lbCount').textContent='Top '+items.length+' on 红果 right now'+(cat!=='all'?(' · '+({human:'Live-action',comic:'Animated',ai:'AI'}[cat]||cat)):'');
        buildPager(1,1);
      } else {
        var from=(d.page-1)*d.size+1, to=(d.page-1)*d.size+items.length;
        $('#lbCount').textContent='Showing '+fmt(from)+'–'+fmt(to)+' of '+fmt(d.count||items.length)+' dramas'+(genre?(' · '+genre):'')+(q?(' · “'+q+'”'):'');
        buildPager(d.page||1, d.pages||1);
      }
      syncURL();
      if(scroll){ var top=$('#lbTabs'); if(top) top.scrollIntoView({block:'start',behavior:'smooth'}); }
    }).catch(function(){ if(my===seq){ grid.innerHTML='<div class="lb-empty">Couldn\'t reach the live feed — please try again shortly.</div>'; } });
  }

  function ensureGenres(){
    if(genresLoaded) return;
    genresLoaded=true;
    fetch(API+'/genres?limit=22').then(function(r){return r.json();}).then(function(d){
      var chips='<button class="lb-chip" type="button" data-g="">All</button>'
        +(d.genres||[]).map(function(g){ return '<button class="lb-chip" type="button" data-g="'+esc(g.value||g.genre)+'">'+esc(g.genre)+'</button>'; }).join('');
      var box=$('#lbGenres'); box.innerHTML=chips;
      box.querySelectorAll('.lb-chip').forEach(function(c){
        c.classList.toggle('on', (c.dataset.g||'')===(genre||''));
        c.onclick=function(){ genre=c.dataset.g||''; q=''; page=1; var si=$('#lbSearch'); if(si) si.value=''; box.querySelectorAll('.lb-chip').forEach(function(x){x.classList.toggle('on',x===c);}); load(); };
      });
    }).catch(function(){ genresLoaded=false; });
  }

  // modal: card detail + saved list
  function closeModal(){ $('#bzModal').classList.remove('open'); }
  function openDetail(id){
    var x=itemsById[id] || (favs[id]?{title:favs[id].t,cover:favs[id].c,episode_cnt:favs[id].e,score:favs[id].s,series_id:id}:null);
    if(!x) return;
    var title=x.title||'', saved=!!favs[id];
    var body='<div class="bz-detail">'
      +'<img src="'+esc(x.cover||'')+'" alt="'+esc(title)+'" onerror="this.style.visibility=\'hidden\'">'
      +'<div><h3>'+esc(title)+'</h3>'
      +'<div class="meta">'+(x.episode_cnt||'?')+' episodes'+(x.score?(' · ★ '+esc(x.score)):'')+(x.status==='completed'?' · Completed':(x.status==='ongoing'?' · Ongoing':''))+'</div>'
      +'<div class="acts">'
        +'<button class="bz-cp" data-cp="title" style="flex:0 0 auto;padding:9px 15px">⧉ Copy title</button>'
        +'<button class="bz-cp" data-cp="link" style="flex:0 0 auto;padding:9px 15px">《》 Copy link</button>'
        +'<button class="bz-fav'+(saved?' on':'')+'" data-fav style="width:auto;padding:9px 15px">'+(saved?'♥ Saved':'♡ Save')+'</button>'
      +'</div>'
      +'<p style="margin:16px 0 0;color:var(--ink-2);font:500 13.5px/1.6 var(--font-ui)">Copy the title or 《》 tag, then paste it into Hongguo Downloader to find this and grab every episode in 1080p.</p>'
      +'<a class="btn primary" style="margin-top:14px" href="'+DL+'">⬇ Download the app</a>'
      +'</div></div>';
    var m=$('#bzModal'); m.dataset.mode='detail'; m.dataset.id=id; $('#bzModalBody').innerHTML=body; m.classList.add('open');
  }
  function openSaved(){
    var ids=Object.keys(favs);
    var body='<h3 class="bz-mh">★ Your saved dramas <span style="color:var(--muted);font-weight:700">('+ids.length+')</span></h3>';
    if(!ids.length){ body+='<p style="margin:14px 0 0;color:var(--ink-2);font:500 14px/1.6 var(--font-ui)">Nothing saved yet. Tap ♥ on any drama to build a list here — then copy them all at once to paste into the app.</p>'; }
    else {
      body+='<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">'
        +'<button class="bz-cp" data-all="title" style="flex:0 0 auto;padding:9px 15px">⧉ Copy all titles</button>'
        +'<button class="bz-cp" data-all="link" style="flex:0 0 auto;padding:9px 15px">《》 Copy all links</button>'
        +'<button class="bz-cp" data-all="clear" style="flex:0 0 auto;padding:9px 15px">Clear all</button>'
        +'</div>';
      body+='<div class="bz-saved-list">'+ids.map(function(id){ return '<div class="bz-saved-row" data-id="'+esc(id)+'"><span>'+esc(favs[id].t||'')+'</span><button data-rm type="button">Remove</button></div>'; }).join('')+'</div>';
    }
    var m=$('#bzModal'); m.dataset.mode='saved'; m.dataset.id=''; $('#bzModalBody').innerHTML=body; m.classList.add('open');
  }
  $('#bzModalBody').addEventListener('click', function(e){
    var m=$('#bzModal');
    var all=e.target.closest('[data-all]');
    if(all){
      var ids=Object.keys(favs);
      if(all.dataset.all==='title'){ copy(ids.map(function(i){return favs[i].t;}).join('\n'), 'Copied '+ids.length+' titles'); }
      else if(all.dataset.all==='link'){ copy(ids.map(function(i){return '《'+favs[i].t+'》';}).join('\n'), 'Copied '+ids.length+' links'); }
      else { favs={}; saveFavs(); renderFavUI(); openSaved(); }
      return;
    }
    var rm=e.target.closest('[data-rm]');
    if(rm){ var row=rm.closest('.bz-saved-row'); if(row){ delete favs[row.dataset.id]; saveFavs(); renderFavUI(); openSaved(); } return; }
    if(m.dataset.mode==='detail'){
      var id=m.dataset.id, x=itemsById[id]||(favs[id]?{title:favs[id].t}:null); if(!x) return; var title=x.title||'';
      var cp=e.target.closest('.bz-cp'); if(cp && cp.dataset.cp){ if(cp.dataset.cp==='link') copy('《'+title+'》','Copied 《'+title.slice(0,16)+(title.length>16?'…':'')+'》'); else copy(title,'Copied title'); return; }
      var fav=e.target.closest('.bz-fav'); if(fav){ toggleFav(id); openDetail(id); return; }
    }
  });
  $('#bzX').onclick=closeModal;
  $('#bzModal').addEventListener('click', function(e){ if(e.target===this) closeModal(); });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeModal(); });
  $('#bzSavedBtn').onclick=openSaved;

  // grid actions: fav / copy / open detail
  $('#lbGrid').addEventListener('click', function(e){
    var fav=e.target.closest('.bz-fav'); if(fav){ var c1=fav.closest('.bz-card'); if(c1) toggleFav(c1.dataset.id); return; }
    var cp=e.target.closest('.bz-cp'); if(cp){ var c2=cp.closest('.bz-card'); var x=c2&&itemsById[c2.dataset.id]; if(!x) return; var t=x.title||''; if(cp.dataset.cp==='link') copy('《'+t+'》','Copied 《'+t.slice(0,16)+(t.length>16?'…':'')+'》'); else copy(t,'Copied title'); return; }
    var art=e.target.closest('.lb-art'); if(art){ var c3=art.closest('.bz-card'); if(c3) openDetail(c3.dataset.id); }
  });
  $('#lbGrid').addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ var art=e.target.closest('.lb-art'); if(art){ e.preventDefault(); var c=art.closest('.bz-card'); if(c) openDetail(c.dataset.id); } } });

  // tabs / filters
  document.querySelectorAll('#lbTabs .lb-tab').forEach(function(t){ t.onclick=function(){
    mode=t.dataset.mode; page=1;
    document.querySelectorAll('#lbTabs .lb-tab').forEach(function(x){x.classList.toggle('on',x===t);});
    $('#lbCats').hidden = mode!=='leaderboard'; $('#lbGenres').hidden = mode!=='catalog'; $('#lbToolbar').hidden = mode!=='catalog';
    if(mode==='catalog') ensureGenres();
    load();
  };});
  document.querySelectorAll('#lbCats .lb-chip').forEach(function(c){ c.onclick=function(){
    cat=c.dataset.cat; page=1; document.querySelectorAll('#lbCats .lb-chip').forEach(function(x){x.classList.toggle('on',x===c);}); load();
  };});
  $('#lbSort').onchange=function(){ sort=this.value; page=1; load(); };
  $('#lbStatus').onchange=function(){ status=this.value; page=1; load(); };
  (function(){ var si=$('#lbSearch'), tm; if(!si) return; si.oninput=function(){ clearTimeout(tm); tm=setTimeout(function(){ q=si.value.trim(); genre=''; page=1; var box=$('#lbGenres'); if(box) box.querySelectorAll('.lb-chip').forEach(function(x){x.classList.toggle('on',(x.dataset.g||'')==='' && !q);}); load(); }, 350); }; })();

  // hero live-stats
  fetch(API+'/explorer?size=1').then(function(r){return r.json();}).then(function(d){
    fetch(API+'/genres?limit=60').then(function(r){return r.json();}).then(function(g){
      var ai=0,an=0; (g.genres||[]).forEach(function(x){ if(x.value==='AI')ai=x.count; if(x.value==='Animated')an=x.count; });
      var el=$('#livestat'); if(el){ el.innerHTML='<b>'+fmt(d.count)+'</b> dramas · <b>'+fmt(ai)+'</b> AI · <b>'+fmt(an)+'</b> animated · live from 红果'; }
    }).catch(function(){});
  }).catch(function(){});

  // init from URL -> reflect into UI -> load
  initFromURL();
  document.querySelectorAll('#lbTabs .lb-tab').forEach(function(x){ x.classList.toggle('on', x.dataset.mode===mode); });
  $('#lbCats').hidden = mode!=='leaderboard'; $('#lbGenres').hidden = mode!=='catalog'; $('#lbToolbar').hidden = mode!=='catalog';
  document.querySelectorAll('#lbCats .lb-chip').forEach(function(c){ c.classList.toggle('on', c.dataset.cat===cat); });
  if(mode==='catalog'){ var ss=$('#lbSort'); if(ss) ss.value=sort; var st=$('#lbStatus'); if(st) st.value=status; var si=$('#lbSearch'); if(si&&q) si.value=q; ensureGenres(); }
  renderFavUI();
  load();
})();
