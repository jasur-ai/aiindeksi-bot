// Raqamlab: eski manzillardan («AI Labs», «Raqamli AI Lab») yangi saytga doimiy yo'naltirish
export default {
  fetch(req) {
    const u = new URL(req.url);
    return Response.redirect("https://raqamlab.tdiu.workers.dev" + u.pathname + u.search, 301);
  },
};
