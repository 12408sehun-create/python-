// (function() {
//   const cache = JSON.parse(localStorage.getItem('tranCache')) || {};
//   const originalTexts = new Map();

//   // 保存页面原始中文（只存一次，防止乱码）
//   window.saveOriginalTexts = function () {
//     originalTexts.clear();
//     const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
//       acceptNode: node => {
//         const p = node.parentElement;
//         if (!p) return NodeFilter.FILTER_REJECT;
//         if (p.tagName === 'SCRIPT' || p.tagName === 'STYLE') return NodeFilter.FILTER_REJECT;
//         if (p.classList.contains('no-translate')) return NodeFilter.FILTER_REJECT;
//         return node.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
//       }
//     });
//     let n;
//     while (n = walker.nextNode()) {
//       if (!originalTexts.has(n)) {
//         originalTexts.set(n, n.textContent.trim());
//       }
//     }
//   };

//   // 翻译接口
//   window.doTranslate = async function (text, to) {
//     if (!text) return text;
//     if (cache[to] && cache[to][text]) return cache[to][text];

//     try {
//       const res = await fetch(`https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=zh-CN|${to}`);
//       const data = await res.json();
//       const trans = data.responseData?.translatedText || text;

//       cache[to] = cache[to] || {};
//       cache[to][text] = trans;
//       localStorage.setItem('tranCache', JSON.stringify(cache));
//       return trans;
//     } catch (e) {
//       return text;
//     }
//   };

//   // 切换语言（保存到本地）
//   window.changeLang = async function (lang) {
//     localStorage.setItem('lang', lang);
//     if (lang === 'zh') {
//       location.reload();
//       return;
//     }
//     if (originalTexts.size === 0) saveOriginalTexts();

//     const texts = Array.from(originalTexts.values());
//     const tasks = texts.map(txt => doTranslate(txt, lang));
//     const results = await Promise.all(tasks);
//     const nodes = Array.from(originalTexts.keys());

//     nodes.forEach((node, i) => {
//       node.textContent = results[i];
//     });
//   };

//   // 👇 这就是关键：页面加载自动翻译
//   window.addEventListener('DOMContentLoaded', () => {
//     saveOriginalTexts();
//     const savedLang = localStorage.getItem('lang');
//     if (savedLang && savedLang !== 'zh') {
//       changeLang(savedLang);
//     }
//   });
// })();




// 每次页面加载会先闪中文 html里先隐藏
// (function() {
//   const cache = JSON.parse(localStorage.getItem('tranCache')) || {};
//   const originalTexts = new Map();

//   window.saveOriginalTexts = function () {
//     originalTexts.clear();
//     const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
//       acceptNode: node => {
//         const p = node.parentElement;
//         if (!p) return NodeFilter.FILTER_REJECT;
//         if (p.tagName === 'SCRIPT' || p.tagName === 'STYLE') return NodeFilter.FILTER_REJECT;
//         if (p.classList.contains('no-translate')) return NodeFilter.FILTER_REJECT;
//         return node.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
//       }
//     });
//     let n;
//     while (n = walker.nextNode()) {
//       if (!originalTexts.has(n)) {
//         originalTexts.set(n, n.textContent.trim());
//       }
//     }
//   };

//   window.doTranslate = async function (text, to) {
//     if (!text) return text;
//     if (cache[to] && cache[to][text]) return cache[to][text];

//     try {
//       const res = await fetch(`https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=zh-CN|${to}`);
//       const data = await res.json();
//       const trans = data.responseData?.translatedText || text;

//       cache[to] = cache[to] || {};
//       cache[to][text] = trans;
//       localStorage.setItem('tranCache', JSON.stringify(cache));
//       return trans;
//     } catch (e) {
//       return text;
//     }
//   };

//   window.changeLang = async function (lang, showAfter = true) {
//     localStorage.setItem('lang', lang);

//     if (lang === 'zh') {
//       Array.from(originalTexts.keys()).forEach((node, i) => {
//         node.textContent = Array.from(originalTexts.values())[i];
//       });
//       document.body.style.visibility = 'visible';
//       return;
//     }

//     if (originalTexts.size === 0) saveOriginalTexts();

//     const texts = Array.from(originalTexts.values());
//     const tasks = texts.map(txt => doTranslate(txt, lang));
//     const results = await Promise.all(tasks);
//     const nodes = Array.from(originalTexts.keys());

//     nodes.forEach((node, i) => {
//       node.textContent = results[i];
//     });

//     if (showAfter) document.body.style.visibility = 'visible';
//   };

//   // 👇 这里是关键：页面一加载就先藏起来，等翻译完再显示
//   document.addEventListener('DOMContentLoaded', () => {
//     // 先保存原文
//     saveOriginalTexts();

//     const savedLang = localStorage.getItem('lang');

//     if (savedLang && savedLang !== 'zh') {
//       // 有保存的语言 → 先翻译，翻译完才显示
//       changeLang(savedLang, true);
//     } else {
//       // 中文 → 直接显示
//       document.body.style.visibility = 'visible';
//     }
//   });
// })();




(function() {
  const cache = JSON.parse(localStorage.getItem('tranCache')) || {};
  const originalTexts = new Map();

  window.saveOriginalTexts = function () {
    originalTexts.clear();
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: node => {
        const p = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        if (p.tagName === 'SCRIPT' || p.tagName === 'STYLE') return NodeFilter.FILTER_REJECT;
        if (p.classList.contains('no-translate')) return NodeFilter.FILTER_REJECT;
         // 👇 新增：跳过带有 no-translate 类名 或 translate="no" 属性的元素
        if (p.classList.contains('no-translate') || p.hasAttribute('translate')) return NodeFilter.FILTER_REJECT;

        const text = node.textContent.trim();
        // 过滤纯数字，避免翻译后显示异常
        if (/^[\d,.]+$/.test(text)) {
          return NodeFilter.FILTER_REJECT;
        }
        
        return text ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    let n;
    while (n = walker.nextNode()) {
      if (!originalTexts.has(n)) {
        originalTexts.set(n, n.textContent.trim());
      }
    }
  };

  // 精准清理警告文本，并兜底保护，避免页面无文字
  function cleanTranslation(text, originalText = '') {
    if (typeof text !== 'string') return text;

    // 1. 精准移除完整的 MYMEMORY 警告块
    text = text.replace(/MYMEMORY WARNING:[\s\S]*?(TO TRANSLATE MORE)?/gi, '');

    // 2. 精准移除额度耗尽的单行警告
    text = text.replace(/YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR TODAY\. NEXT AVAILABLE IN \d+ HOURS \d+ MINUTES \d+ SECONDS VISIT HTTPS?:\/\/[^\s]+ TO TRANSLATE MORE/gi, '');

    // 3. 移除孤立的 URL 链接
    text = text.replace(/https?:\/\/[^\s]+/g, '');

    // 4. 清理多余空格和换行
    text = text.replace(/\s+/g, ' ').trim();

    // 5. 兜底保护：如果清理后为空，返回原始中文，保证页面有字
    if (text === '' && originalText !== '') {
      return originalText;
    }

    return text;
  }

  // 兜底：全页面扫描清理，确保无遗漏
  function scanAndCleanAllText() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: node => {
        if (node.parentElement.tagName === 'SCRIPT' || node.parentElement.tagName === 'STYLE') {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    let n;
    while (n = walker.nextNode()) {
      const original = n.textContent;
      const cleaned = cleanTranslation(original);
      if (original !== cleaned) {
        n.textContent = cleaned;
      }
    }
  }

  window.doTranslate = async function (text, to) {
    if (!text) return text;
    if (cache[to] && cache[to][text]) {
      return cleanTranslation(cache[to][text], text);
    }

    try {
      // 替换成你的邮箱，提升额度到 50,000 字符/天
      const EMAIL = "1240847112@qq.com";
      const encodedEmail = encodeURIComponent(EMAIL);

      const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=zh-CN|${to}&de=${encodedEmail}`;

      const res = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
      });

      const data = await res.json();
      let trans = data.responseData?.translatedText || text;
      trans = cleanTranslation(trans, text);

      cache[to] = cache[to] || {};
      cache[to][text] = trans;
      localStorage.setItem('tranCache', JSON.stringify(cache));
      return trans;
    } catch (e) {
      return text; // 翻译失败返回原始中文，不显示乱码
    }
  };

  window.changeLang = async function (lang, showAfter = true) {
    localStorage.setItem('lang', lang);

    if (lang === 'zh') {
      Array.from(originalTexts.keys()).forEach((node, i) => {
        node.textContent = Array.from(originalTexts.values())[i];
      });
      scanAndCleanAllText(); // 兜底清理
      document.body.style.visibility = 'visible';
      return;
    }

    if (originalTexts.size === 0) saveOriginalTexts();

    const texts = Array.from(originalTexts.values());
    const tasks = texts.map(txt => doTranslate(txt, lang));
    const results = await Promise.all(tasks);
    const nodes = Array.from(originalTexts.keys());

    nodes.forEach((node, i) => {
      const originalText = texts[i];
      node.textContent = cleanTranslation(results[i], originalText);
    });

    scanAndCleanAllText(); // 兜底清理
    if (showAfter) document.body.style.visibility = 'visible';
  };

  document.addEventListener('DOMContentLoaded', () => {
    saveOriginalTexts();
    const savedLang = localStorage.getItem('lang');

    if (savedLang && savedLang !== 'zh') {
      changeLang(savedLang, true).then(() => {
        scanAndCleanAllText(); // 再次兜底，确保无遗漏
      });
    } else {
      scanAndCleanAllText();
      document.body.style.visibility = 'visible';
    }
  });
})();


// (function() {
//   const cache = JSON.parse(localStorage.getItem('tranCache')) || {};
//   const originalTexts = new Map();

//   window.saveOriginalTexts = function () {
//     originalTexts.clear();
//     const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
//       acceptNode: node => {
//         const p = node.parentElement;
//         if (!p) return NodeFilter.FILTER_REJECT;
//         if (p.tagName === 'SCRIPT' || p.tagName === 'STYLE') return NodeFilter.FILTER_REJECT;
//         if (p.classList.contains('no-translate')) return NodeFilter.FILTER_REJECT;
//         return node.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
//       }
//     });
//     let n;
//     while (n = walker.nextNode()) {
//       if (!originalTexts.has(n)) {
//         originalTexts.set(n, n.textContent.trim());
//       }
//     }
//   };

//   // 终极版清理：精准拦截所有出现的警告文本
//   function cleanTranslation(text) {
//     if (typeof text !== 'string') return text;
    
//     // 1. 精准拦截你提到的这句警告
//     text = text.replace(/YOU FOR TODAY\.?\s*\d+ HOURS \d+ MINUTES \d+ SECONDS\s*VISIT HTTPS?:\/\/[^\s]+/gi, '');
    
//     // 2. 拦截 MYMEMORY 核心警告
//     text = text.replace(/MYMEMORY WARNING:[\s\S]*?(TO TRANSLATE MORE)?/gi, '');
    
//     // 3. 拦截额度耗尽相关关键词
//     text = text.replace(/\b(USED ALL AVAILABLE FREE TRANSLATIONS|NEXT AVAILABLE IN|USAGELIMITS\.PHP|TRANSLATED\.NET|TO TRANSLATE MORE)\b/gi, '');
    
//     // 4. 移除所有 URL 链接
//     text = text.replace(/https?:\/\/[^\s]+/g, '');
    
//     // 5. 清理多余的换行、空格和标点
//     text = text.replace(/\n+/g, ' ').replace(/\s+/g, ' ').replace(/^\W+|\W+$/g, '').trim();
    
//     return text;
//   }

//   // 兜底：翻译完成后全页面扫描清理
//   function scanAndCleanAllText() {
//     const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
//       acceptNode: node => {
//         if (node.parentElement.tagName === 'SCRIPT' || node.parentElement.tagName === 'STYLE') {
//           return NodeFilter.FILTER_REJECT;
//         }
//         return NodeFilter.FILTER_ACCEPT;
//       }
//     });
//     let n;
//     while (n = walker.nextNode()) {
//       const original = n.textContent;
//       const cleaned = cleanTranslation(original);
//       if (original !== cleaned) {
//         n.textContent = cleaned;
//       }
//     }
//   }

//   window.doTranslate = async function (text, to) {
//     if (!text) return text;
//     if (cache[to] && cache[to][text]) {
//       return cleanTranslation(cache[to][text]);
//     }

//     try {
//       // 替换成你的邮箱，提升额度到 50,000 字符/天
//       const EMAIL = "1240847112@qq.com";
//       const encodedEmail = encodeURIComponent(EMAIL);

//       const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=zh-CN|${to}&de=${encodedEmail}`;

//       const res = await fetch(url, {
//         headers: {
//           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
//         }
//       });

//       const data = await res.json();
//       let trans = data.responseData?.translatedText || text;
//       trans = cleanTranslation(trans);

//       cache[to] = cache[to] || {};
//       cache[to][text] = trans;
//       localStorage.setItem('tranCache', JSON.stringify(cache));
//       return trans;
//     } catch (e) {
//       return text; // 翻译失败返回原始中文，不显示乱码
//     }
//   };

//   window.changeLang = async function (lang, showAfter = true) {
//     localStorage.setItem('lang', lang);

//     if (lang === 'zh') {
//       Array.from(originalTexts.keys()).forEach((node, i) => {
//         node.textContent = Array.from(originalTexts.values())[i];
//       });
//       scanAndCleanAllText(); // 兜底清理
//       document.body.style.visibility = 'visible';
//       return;
//     }

//     if (originalTexts.size === 0) saveOriginalTexts();

//     const texts = Array.from(originalTexts.values());
//     const tasks = texts.map(txt => doTranslate(txt, lang));
//     const results = await Promise.all(tasks);
//     const nodes = Array.from(originalTexts.keys());

//     nodes.forEach((node, i) => {
//       node.textContent = cleanTranslation(results[i]);
//     });

//     scanAndCleanAllText(); // 兜底清理
//     if (showAfter) document.body.style.visibility = 'visible';
//   };

//   document.addEventListener('DOMContentLoaded', () => {
//     saveOriginalTexts();
//     const savedLang = localStorage.getItem('lang');

//     if (savedLang && savedLang !== 'zh') {
//       changeLang(savedLang, true).then(() => {
//         scanAndCleanAllText(); // 再次兜底，确保无遗漏
//       });
//     } else {
//       scanAndCleanAllText();
//       document.body.style.visibility = 'visible';
//     }
//   });
// })();