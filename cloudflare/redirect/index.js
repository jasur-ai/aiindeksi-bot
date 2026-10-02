// Raqamlab: eski manzillardan (raqamlab/raqamli/ailabs.tdiu.workers.dev) asosiy saytga doimiy yo'naltirish
export default {
  fetch(req) {
    const u = new URL(req.url);
    return Response.redirect("https://raqamlab.pages.dev" + u.pathname + u.search, 301);
  },
};
