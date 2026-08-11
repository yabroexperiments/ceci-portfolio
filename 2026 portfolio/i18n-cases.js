/* =========================================================================
   Ceci Chang — Portfolio i18n（案例研究頁專用字典）
   -------------------------------------------------------------------------
   這個檔案「疊加」在 i18n.js 之上,不會覆蓋 i18n.js 的任何內容。
   所以 i18n.js 你可以自由編輯,兩個檔案互不干擾。

   載入順序很重要,HTML 裡必須是這個順序:
     <script src="i18n.js"></script>
     <script src="i18n-cases.js"></script>

   編輯方式跟 i18n.js 完全一樣:只改引號中間的文字,不要改 key。
   zh 留空的話會自動顯示英文,不會變空白。
   ========================================================================= */

(function () {
  if (!window.I18N_DICT) window.I18N_DICT = {};

  var ADD = {

    /* ---------- 案例頁共用欄位標籤 ---------- */
    'fact.role':       { en: 'Role',      zh: '角色' },
    'fact.scope':      { en: 'Scope',     zh: '範圍' },
    'fact.year':       { en: 'Year',      zh: '年份' },
    'fact.teams':      { en: 'Teams',     zh: '協作團隊' },
    'strip.product':   { en: 'Product',   zh: '產品' },
    'strip.ownership': { en: 'Ownership', zh: '負責範圍' },
    'strip.impact':    { en: 'Impact',    zh: '成果' },

    /* ---------- 卡片按鈕（若 i18n.js 已定義,以 i18n.js 為優先）---------- */
    'tag.visit': { en: 'Visit Site', zh: '前往網站' },

    /* ---------- TraderWagon：頁首 ---------- */
    'cs.tw.short': { en: 'Social Trading Platform', zh: '社交交易平台' },
    'cs.tw.long':  { en: 'TraderWagon Social Trading Platform', zh: 'TraderWagon 社交交易平台' },

    'tw.chip2': { en: 'Social Trading', zh: '社交交易' },
    'tw.title': { en: 'TraderWagon Social Trading Platform',
                  zh: 'TraderWagon 社交交易平台' },
    'tw.lead':  { en: 'TraderWagon is a social crypto trading platform that helps beginners find experienced traders and copy their trades. Users sign in with their Binance credentials, and can also reach the product as a third-party app embedded inside Binance.',
                  zh: 'TraderWagon 是一個社交加密貨幣交易平台，協助新手找到有經驗的交易者並跟隨其交易。使用者可用 Binance 帳號登入，也能透過嵌入在 Binance 內的第三方應用使用這個產品。' },

    'tw.role':      { en: 'Design Lead & Product Designer', zh: '設計主管兼產品設計師' },
    'tw.scope':     { en: 'Platform (Web), Binance third-party app, design system',
                      zh: '平台（網頁）、Binance 第三方應用、設計系統' },
    'tw.teams':     { en: '2\u20134 designers, PM, Dev, Marketing',
                      zh: '2\u20134 位設計師、產品經理、工程、行銷' },
    'tw.product':   { en: 'TraderWagon Social Trading (Web & Binance embedded app)',
                      zh: 'TraderWagon 社交交易（網頁與 Binance 嵌入式應用）' },
    'tw.ownership': { en: 'Design lead for the platform, design system, and the Binance third-party app',
                      zh: '負責平台、設計系統與 Binance 第三方應用的設計主導' },
    'tw.impact':    { en: 'Journey-mapping fixes drove a 30% increase in users; the most popular copy trading tool before Binance launched its own.',
                      zh: '依旅程地圖找出的問題修正後帶來 30% 使用者成長；在 Binance 推出自有功能前，是最受歡迎的跟單交易工具。' },

    /* ---------- TraderWagon：章節名稱 ---------- */
    'tw.toc1': { en: 'My Role',                zh: '我的角色' },
    'tw.toc2': { en: 'User Journey Map',       zh: '使用者旅程地圖' },
    'tw.toc3': { en: 'Web Design',             zh: '網頁設計' },
    'tw.toc4': { en: 'User Feedback Loop',     zh: '使用者回饋機制' },
    'tw.toc5': { en: 'Binance 3rd Party Tool', zh: 'Binance 第三方工具' },

    /* ---------- TraderWagon：01 My Role ---------- */
    'tw.s1.h':  { en: 'Leading a small design team across the platform, the design system, and social.',
                  zh: '帶領小型設計團隊，橫跨平台、設計系統與社群。' },
    'tw.s1.p1': { en: 'As Design Lead for TraderWagon I led a team of 2\u20134 designers covering both the platform and the social media experience. My work was as much about building the system the team designed within as about the screens themselves.',
                  zh: '作為 TraderWagon 的設計主管，我帶領 2\u20134 位設計師，負責平台與社群媒體體驗。我的工作除了畫面本身，更重要的是建立團隊得以在其中工作的設計體系。' },
    'tw.s1.p2': { en: 'I directed the team to establish design guidelines, a shared component library, and page flows, and I ran the reviews that kept the experience consistent as the product grew.',
                  zh: '我帶領團隊建立設計規範、共用元件庫與頁面流程，並主持設計審查，讓產品持續擴張的同時體驗仍保持一致。' },

    /* ---------- TraderWagon：02 User Journey Map ---------- */
    'tw.s2.h':  { en: 'Mapping the journey to find where beginners actually got stuck.',
                  zh: '繪製旅程地圖，找出新手真正卡住的地方。' },
    'tw.s2.p1': { en: 'I ran workshops and interviews to map the end-to-end journey and locate the specific steps where users ran into trouble, rather than guessing from analytics alone. Resolving the problems surfaced by that exercise led to a 30% increase in users.',
                  zh: '我透過工作坊與使用者訪談繪製完整旅程，定位出使用者實際遇到問題的具體步驟，而不是只憑數據推測。修正這個過程中浮現的問題後，使用者成長了 30%。' },
    'tw.s2.c1': { en: 'User journey map from workshops and interviews',
                  zh: '由工作坊與訪談產出的使用者旅程地圖' },

    /* ---------- TraderWagon：03 Web Design ---------- */
    'tw.s3.h':  { en: 'Shifting visual focus onto the portfolios people came to compare.',
                  zh: '把視覺重心移回使用者真正要比較的投組上。' },
    'tw.s3.g0': { en: 'Overview',                zh: '整體概覽' },
    'tw.s3.c0': { en: 'Web design overview',     zh: '網頁設計概覽' },
    'tw.s3.g1': { en: 'Homepage & filters',      zh: '首頁與篩選器' },
    'tw.s3.l1a':{ en: 'Reduced the height of the activity banner so visual focus lands on the portfolio cards.',
                  zh: '降低活動橫幅的高度，讓視覺重心落在投組卡片上。' },
    'tw.s3.l1b':{ en: 'Improved the usability of the filters.', zh: '改善篩選器的易用性。' },
    'tw.s3.l1c':{ en: 'Moved My Favorites to a more visible location to increase its usage.',
                  zh: '將「我的收藏」移到更顯眼的位置，提升使用率。' },
    'tw.s3.l1d':{ en: 'Increased the number of portfolio cards on the first page from 9 to 20.',
                  zh: '首頁的投組卡片數量從 9 張增加到 20 張。' },
    'tw.s3.l1e':{ en: 'Added more sorting options and API filters.',
                  zh: '新增更多排序選項與 API 篩選條件。' },
    'tw.s3.c1': { en: 'Homepage & filter iteration', zh: '首頁與篩選器的迭代' },
    'tw.s3.g2': { en: 'Copy Settings page',      zh: '跟單設定頁' },
    'tw.s3.l2a':{ en: 'Reduced how often users had to go back to the previous page.',
                  zh: '減少使用者需要退回上一頁的次數。' },
    'tw.s3.l2b':{ en: 'Removed illustrations to make room for the settings that mattered.',
                  zh: '移除插圖，把空間留給真正重要的設定項目。' },
    'tw.s3.l2c':{ en: 'Added friendlier guidance for first-time users.',
                  zh: '為初次使用者加入更友善的提示說明。' },
    'tw.s3.l2d':{ en: 'Promoted take-profit and stop-loss to the first layer, based on user feedback.',
                  zh: '依使用者回饋，把止盈與止損提升到第一層。' },
    'tw.s3.c2': { en: 'Copy Settings iteration', zh: '跟單設定頁的迭代' },

    /* ---------- TraderWagon：04 User Feedback Loop ---------- */
    'tw.s4.h':  { en: 'Turning social media complaints into a weekly design intake.',
                  zh: '把社群上的抱怨，變成每週固定的設計輸入。' },
    'tw.s4.p1': { en: 'Rather than treating social media as noise, my team reviewed and validated user feedback and reported issues there every week. Once priorities were agreed with the other teams, the fixes went straight into the design queue.',
                  zh: '我們沒有把社群輿論當成雜訊，而是每週檢視並驗證上面的使用者回饋與問題回報。與其他團隊確認優先順序後，這些修正就直接進入設計排程。' },
    'tw.s4.c1': { en: 'Weekly review of user feedback from social media',
                  zh: '每週檢視來自社群媒體的使用者回饋' },

    /* ---------- TraderWagon：05 Binance 3rd Party Tool ---------- */
    'tw.s5.h':  { en: 'The same product, embedded inside Binance itself.',
                  zh: '同一個產品，直接嵌進 Binance 裡。' },
    'tw.s5.p1': { en: 'This third-party tool was an app embedded on the Binance homepage, letting users copy trade directly with their Binance wallet. It was the most popular copy trading tool available before Binance built its own feature.',
                  zh: '這個第三方工具是嵌在 Binance 首頁上的應用，讓使用者能直接用自己的 Binance 錢包跟單。在 Binance 推出自有功能之前，它是市場上最受歡迎的跟單交易工具。' },
    'tw.s5.g1': { en: 'Homepage',   zh: '首頁' },
    'tw.s5.c1': { en: 'Browsing Lead Trader portfolios to find one to invest in',
                  zh: '瀏覽帶單交易者的投組，找到想投入的標的' },
    'tw.s5.g2': { en: 'Onboarding', zh: '新手引導' },
    'tw.s5.c2': { en: 'Welcome guide and sign-up with a Binance wallet',
                  zh: '歡迎引導與使用 Binance 錢包註冊' },
    'tw.s5.g3': { en: 'Portfolio & copying', zh: '投組與跟單' },
    'tw.s5.c3': { en: 'Portfolio Details and Copy Portfolio pages',
                  zh: '投組詳情頁與跟單投組頁' },
    'tw.s5.g4': { en: 'Managing your copies', zh: '管理你的跟單' },
    'tw.s5.c4': { en: 'My Copy Trading \u2014 managing portfolios and adjusting copy settings',
                  zh: '我的跟單交易 \u2014 管理投組與調整跟單設定' },

    /* ---------- 下拉選單新增項目 ---------- */
    'cs.lb.short': { en: 'Leaderboard',             zh: '排行榜' },
    'cs.lb.long':  { en: 'BINANCE Social Trading Leaderboard', zh: 'BINANCE 社交交易排行榜' },

    /* ---------- Leaderboard：頁首 ---------- */
    'lb.eyebrow': { en: 'Case Study',    zh: '案例研究' },
    'lb.chip2':   { en: 'Social Trading', zh: '社交交易' },
    'lb.title':   { en: 'BINANCE Social Trading Leaderboard',
                    zh: 'BINANCE 社交交易排行榜' },
    'lb.lead':    { en: 'The Futures Leaderboard ranks traders on Binance by criteria such as ROI, PnL, and popularity within a given time period — turning individual performance into a public signal that drives competition and trader discovery.',
                    zh: '合約排行榜依據 ROI、盈虧與人氣等指標，對 Binance 上的交易者在特定時間區間內進行排名，把個人績效轉化為公開訊號，帶動競爭並協助使用者發現值得追蹤的交易者。' },

    'lb.role':      { en: 'Product Designer', zh: '產品設計師' },
    'lb.scope':     { en: 'Leaderboard (Web & App), Options & Trading Bot Leaderboards',
                      zh: '排行榜（網頁與 App）、選擇權與交易機器人排行榜' },
    'lb.teams':     { en: 'PM, Dev, Marketing', zh: '產品經理、工程、行銷' },
    'lb.product':   { en: 'Futures Leaderboard (Web & App)', zh: '合約排行榜（網頁與 App）' },
    'lb.ownership': { en: 'Ranking system, trader profiles, follow & notifications',
                      zh: '排名機制、交易者個人頁、追蹤與通知' },
    'lb.impact':    { en: 'Became a key indicator for Binance Futures competition campaigns.',
                      zh: '成為 Binance 合約競賽活動的核心指標。' },

    /* ---------- Leaderboard：章節名稱 ---------- */
    'lb.toc1': { en: 'My Role',     zh: '我的角色' },
    'lb.toc2': { en: 'App Design',  zh: 'App 設計' },
    'lb.toc3': { en: 'Web Design',  zh: '網頁設計' },

    /* ---------- Leaderboard：01 My Role ---------- */
    'lb.s1.h':  { en: 'Turning a plain ranking list into the signal that drives Futures competition.',
                  zh: '把一張單調的排名清單，變成帶動合約競賽的關鍵訊號。' },
    'lb.s1.p1': { en: 'The old Futures Leaderboard was a simple ranking of futures traders — little more than a table of numbers. When I took ownership of the product, I rebuilt its visual style and user flows, and extended it with new categories such as the Options and Trading Bot Leaderboards.',
                  zh: '舊版合約排行榜只是一份交易者的簡單排名，幾乎就是一張數字表格。在我接手這個產品後，我重建了它的視覺風格與使用流程，並擴充出選擇權、交易機器人等新的排行榜類別。' },
    'lb.s1.p2': { en: 'It has since become a key indicator for Binance Futures competition campaigns, and a primary way for users to discover traders worth following.',
                  zh: '此後它成為 Binance 合約競賽活動的核心指標，也是使用者發現值得追蹤的交易者的主要入口。' },

    /* ---------- Leaderboard：02 App Design ---------- */
    'lb.s2.h':  { en: 'Designing the mobile experience around discovery, profiles, and following.',
                  zh: '以「發現、個人頁、追蹤」三件事為軸心設計行動端體驗。' },
    'lb.s2.p1': { en: 'The app flow is built around four moments: arriving at the leaderboard, scanning and filtering the ranking, managing your own public profile, and following a trader you want to keep watching.',
                  zh: 'App 的流程圍繞四個關鍵時刻：進入排行榜、瀏覽與篩選排名、管理自己的公開個人頁，以及追蹤想持續關注的交易者。' },

    'lb.s2.g1': { en: 'Entry page & homepage',            zh: '入口頁與首頁' },
    'lb.s2.c1': { en: 'Entry page / Homepage',            zh: '入口頁 / 首頁' },
    'lb.s2.g2': { en: 'Ranking, filtering & following',   zh: '排名、篩選與追蹤' },
    'lb.s2.c2': { en: 'Top Traders Ranking page / Action Sheet / My Following page',
                  zh: '頂尖交易者排名頁 / 操作面板 / 我的追蹤' },
    'lb.s2.g3': { en: 'Your own profile & sharing',       zh: '個人頁與分享' },
    'lb.s2.c3': { en: 'My Profile page / Preferences / Share Post',
                  zh: '我的個人頁 / 偏好設定 / 分享貼文' },
    'lb.s2.g4': { en: 'Trader details & notifications',   zh: '交易者詳情與通知' },
    'lb.s2.c4': { en: 'Trader\u2019s Details page / Follow List / Enable Notifications',
                  zh: '交易者詳情頁 / 追蹤清單 / 開啟通知' },

    /* ---------- Leaderboard：03 Web Design ---------- */
    'lb.s3.h':    { en: 'Carrying the same ranking logic onto a wider, data-dense web layout.',
                    zh: '把同一套排名邏輯，延伸到更寬、資訊密度更高的網頁版面。' },
    'lb.s3.p1':   { en: 'On web there is room to show more of the ranking at once, so the layout leads with the full table while keeping the same filters, time periods, and profile entry points as the app.',
                    zh: '網頁的空間足以一次呈現更多排名，因此版面以完整表格為主，同時保留與 App 一致的篩選器、時間區間與個人頁入口。' },
    'lb.s3.c1':   { en: 'Web key screen', zh: '網頁主要畫面' },
    'lb.s3.link': { en: 'See the live Leaderboard on Binance',
                    zh: '前往 Binance 查看實際排行榜' }
  };

  /* 疊加進主字典（不覆蓋 i18n.js 已定義的同名 key） */
  for (var k in ADD) {
    if (Object.prototype.hasOwnProperty.call(ADD, k) && !window.I18N_DICT[k]) {
      window.I18N_DICT[k] = ADD[k];
    }
  }
})();
