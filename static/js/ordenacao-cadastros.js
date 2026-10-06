(function(){
  'use strict';

  function itensDo(container, seletor){
    return Array.from(container.querySelectorAll(seletor)).filter(function(el){
      return el.parentElement === container;
    });
  }

  function grupoDo(item){
    return item && item.dataset ? (item.dataset.sortGroup || '') : '';
  }

  function atualizarPosicoes(container, seletor){
    var grupos = Object.create(null);
    itensDo(container, seletor).forEach(function(item){
      var grupo = grupoDo(item);
      (grupos[grupo] || (grupos[grupo] = [])).push(item);
    });
    Object.keys(grupos).forEach(function(grupo){
      grupos[grupo].forEach(function(item, indice){
        var pos = item.querySelector('[data-posicao]');
        if(pos) pos.textContent = (indice + 1) + 'º';
        var subir = item.querySelector('[data-move="cima"]');
        var descer = item.querySelector('[data-move="baixo"]');
        if(subir) subir.disabled = indice === 0;
        if(descer) descer.disabled = indice === grupos[grupo].length - 1;
      });
    });
  }

  function avisarMudanca(container){
    container.dispatchEvent(new CustomEvent('ordenacao:alterada', {bubbles:true}));
  }

  function init(container, opcoes){
    if(!container || container.dataset.sortableReady === '1') return;
    container.dataset.sortableReady = '1';

    opcoes = opcoes || {};
    var itemSelector = opcoes.itemSelector || '[data-sortable-item]';
    var handleSelector = opcoes.handleSelector || '[data-drag-handle]';
    var arraste = null;

    function podeTrocar(a, b){
      return a && b && a !== b && a.parentElement === container && b.parentElement === container && grupoDo(a) === grupoDo(b);
    }

    function moverPorBotao(item, direcao){
      var grupo = grupoDo(item);
      var grupoItens = itensDo(container, itemSelector).filter(function(x){ return grupoDo(x) === grupo; });
      var indice = grupoItens.indexOf(item);
      if(indice < 0) return;
      if(direcao === 'cima' && indice > 0){
        grupoItens[indice - 1].before(item);
      }else if(direcao === 'baixo' && indice < grupoItens.length - 1){
        grupoItens[indice + 1].after(item);
      }else{
        return;
      }
      atualizarPosicoes(container, itemSelector);
      avisarMudanca(container);
    }

    container.addEventListener('click', function(e){
      var botao = e.target.closest('[data-move]');
      if(!botao || !container.contains(botao)) return;
      e.preventDefault();
      moverPorBotao(botao.closest(itemSelector), botao.dataset.move);
    });

    container.querySelectorAll(handleSelector).forEach(function(handle){
      handle.addEventListener('pointerdown', function(e){
        if(e.pointerType === 'mouse' && e.button !== 0) return;
        var item = handle.closest(itemSelector);
        if(!item) return;
        arraste = {
          item:item,
          handle:handle,
          pointerId:e.pointerId,
          alterou:false,
          pointerEvents:item.style.pointerEvents || ''
        };
        item.classList.add('ordenando');
        document.body.classList.add('ordenacao-ativa');
        item.style.pointerEvents = 'none';
        try{ handle.setPointerCapture(e.pointerId); }catch(_e){}
        e.preventDefault();
      });

      handle.addEventListener('pointermove', function(e){
        if(!arraste || arraste.handle !== handle || arraste.pointerId !== e.pointerId) return;
        e.preventDefault();

        var alvo = document.elementFromPoint(e.clientX, e.clientY);
        alvo = alvo && alvo.closest ? alvo.closest(itemSelector) : null;
        if(podeTrocar(arraste.item, alvo)){
          var rect = alvo.getBoundingClientRect();
          var antes = e.clientY < rect.top + (rect.height / 2);
          if(antes){
            alvo.before(arraste.item);
          }else{
            alvo.after(arraste.item);
          }
          arraste.alterou = true;
          atualizarPosicoes(container, itemSelector);
        }

        var margem = 72;
        if(e.clientY < margem){
          window.scrollBy({top:-14, behavior:'auto'});
        }else if(e.clientY > window.innerHeight - margem){
          window.scrollBy({top:14, behavior:'auto'});
        }
      });

      function finalizar(e){
        if(!arraste || arraste.handle !== handle || (e && arraste.pointerId !== e.pointerId)) return;
        var mudou = arraste.alterou;
        arraste.item.style.pointerEvents = arraste.pointerEvents;
        arraste.item.classList.remove('ordenando');
        document.body.classList.remove('ordenacao-ativa');
        try{ handle.releasePointerCapture(arraste.pointerId); }catch(_e){}
        arraste = null;
        atualizarPosicoes(container, itemSelector);
        if(mudou) avisarMudanca(container);
      }

      handle.addEventListener('pointerup', finalizar);
      handle.addEventListener('pointercancel', finalizar);
    });

    atualizarPosicoes(container, itemSelector);
  }

  window.HumiatSortable = {init:init, atualizarPosicoes:atualizarPosicoes};
})();
