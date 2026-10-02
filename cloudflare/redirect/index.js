// Raqamli AI Lab: eski «AI Labs» manzilidan yangi saytga doimiy yo'naltirish
export default {
  fetch(req) {
    const u = new URL(req.url);
    return Response.redirect("https://raqamli.tdiu.workers.dev" + u.pathname + u.search, 301);
  },
};
