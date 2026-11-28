/* phone swipe left/right = next/previous bundle (same as the 다음 묶음/이전 묶음 buttons); decided during the move, no waiting for the finger to lift */
(function(){let sx=0,sy=0,st=0,ok=false,done=false;
 const hscroll=el=>{for(;el&&el!==document.body;el=el.parentElement){if(el.scrollWidth>el.clientWidth+4){const o=getComputedStyle(el).overflowX;if(o==="auto"||o==="scroll")return true}}return false};
 document.addEventListener("touchstart",e=>{ok=false;done=false;if(e.touches.length!==1)return;const t=e.touches[0],w=innerWidth;if(t.clientX<24||t.clientX>w-24)return;/* leave screen edges to the browser back/forward gesture */
  const el=e.target;if(el.closest&&el.closest("input,select,textarea,#player,.gal,.bsel,#groups,#subs,.subs,.tabs,.ddl"))return;if(hscroll(el))return;sx=t.clientX;sy=t.clientY;st=Date.now();ok=true},{passive:true});
 const go=dx=>{const b=document.querySelector(dx<0?".nextbun:not(.prevbun)":".nextbun.prevbun");if(!b)return;b.click();
  const s2=document.getElementById("sheet");if(s2){s2.style.transition="none";s2.style.transform="translateX("+(dx<0?36:-36)+"px)";s2.style.opacity=".4";requestAnimationFrame(()=>requestAnimationFrame(()=>{s2.style.transition="transform .16s,opacity .16s";s2.style.transform="";s2.style.opacity=""}))}};
 const judge=t=>{if(!ok||done)return;const dx=t.clientX-sx,dy=t.clientY-sy;
  if(Math.abs(dy)>40){ok=false;return}/* vertical scroll */
  if(Date.now()-st>1000){ok=false;return}
  if(Math.abs(dx)<60||Math.abs(dx)<Math.abs(dy)*1.5)return;
  try{const s=getSelection();if(s&&String(s).length){ok=false;return}}catch(_){}
  done=true;ok=false;go(dx)};
 document.addEventListener("touchmove",e=>{if(e.touches.length===1)judge(e.touches[0])},{passive:true});
 document.addEventListener("touchend",e=>{if(ok&&!done)judge(e.changedTouches[0]);ok=false},{passive:true})})();
