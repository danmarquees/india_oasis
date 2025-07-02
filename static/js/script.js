// ======================================================
// ESTADO DA APLICAÇÃO
// ======================================================
let cartItems = [];
let wishlistItems = [];
let currentSlide = 0;

// ======================================================
// SELETORES DE ELEMENTOS DO DOM
// ======================================================
const mainContent = document.getElementById("main-content");
const pages = document.querySelectorAll(".page");
const navLinks = document.querySelectorAll(".nav-link");
const cartCountEl = document.getElementById("cart-count");
const wishlistCountEl = document.getElementById("wishlist-count");
const wishlistBtn = document.getElementById("wishlist-btn");
const cartBtn = document.getElementById("cart-btn");

// Menu Lateral
const sideMenu = document.getElementById("side-menu");
const menuOverlay = document.getElementById("menu-overlay");
const openMenuBtn = document.getElementById("open-menu-btn");
const closeMenuBtn = document.getElementById("close-menu-btn");

// Debug: Verificar se elementos foram encontrados
console.log("🔍 Verificando elementos do menu:");
console.log("- sideMenu:", !!sideMenu, sideMenu);
console.log("- menuOverlay:", !!menuOverlay, menuOverlay);
console.log("- openMenuBtn:", !!openMenuBtn, openMenuBtn);
console.log("- closeMenuBtn:", !!closeMenuBtn, closeMenuBtn);

// Carrossel - Variáveis e Configuração
const carouselItems = document.querySelectorAll(".carousel-item");
const carouselIndicators = document.querySelectorAll(".carousel-indicator");
const carouselProgress = document.getElementById("carousel-progress");
const carouselContainer = document.getElementById("carousel-container");
const nextBtn = document.getElementById("next-slide");
const prevBtn = document.getElementById("prev-slide");
const totalSlides = carouselItems.length;
let carouselInterval;
let isCarouselPaused = false;
let touchStartX = 0;
let touchEndX = 0;
let carouselDebounceTimer = null;
let isCarouselTransitioning = false;

// Debug do carrossel
console.log("🎠 Carrossel Debug:");
console.log("- carouselItems:", carouselItems.length);
console.log("- carouselIndicators:", carouselIndicators.length);
console.log("- carouselProgress:", !!carouselProgress);
console.log("- carouselContainer:", !!carouselContainer);
console.log("- nextBtn:", !!nextBtn);
console.log("- prevBtn:", !!prevBtn);

// ======================================================
// FUNÇÕES DE RENDERIZAÇÃO
// ======================================================

// Renderiza um único card de produto
function createProductCard(product) {
  const isWishlisted = wishlistItems.includes(product.id);
  const wishlistedClass = isWishlisted ? "text-primary" : "text-gray-300";

  return `
            <div class="bg-white rounded-lg shadow-md overflow-hidden group transform hover:-translate-y-2 transition-transform duration-300">
                <div class="relative">
                    <img src="${product.image}" alt="${product.name}" class="w-full h-56 object-cover cursor-pointer product-link" data-id="${product.id}">
                    <button class="wishlist-toggle absolute top-2 right-2 bg-white rounded-full p-2 shadow-md hover:text-primary ${wishlistedClass}" data-id="${product.id}">
                        <i class="fas fa-heart text-xl"></i>
                    </button>
                </div>
                <div class="p-4">
                    <h3 class="text-xl font-teko h-12 cursor-pointer product-link" data-id="${product.id}">${product.name}</h3>
                    <div class="flex justify-between items-center mt-2">
                        <p class="text-lg font-bold text-primary">R$ ${product.price.toFixed(2)}</p>
                        <div class="rating">
                            ${renderStars(product.rating, false)}
                        </div>
                    </div>
                    <button class="add-to-cart-btn btn btn-secondary w-full mt-4" data-id="${product.id}">Adicionar ao Carrinho</button>
                </div>
            </div>
        `;
}

// Renderiza estrelas de avaliação
function renderStars(rating, isInteractive = false) {
  let starsHtml = "";
  for (let i = 1; i <= 5; i++) {
    const starClass = i <= rating ? "text-accent" : "";
    const interactiveAttr = isInteractive ? `data-value="${i}"` : "";
    starsHtml += `<i class="fa-solid fa-star ${starClass}" ${interactiveAttr}></i>`;
  }
  return starsHtml;
}

// Renderiza a página de detalhes do produto
function renderProductDetail(productId) {
  const product = products.find((p) => p.id === productId);
  if (!product) return;

  const isWishlisted = wishlistItems.includes(product.id);
  const wishlistedClass = isWishlisted ? "text-primary" : "text-gray-400";

  const container = document.getElementById("product-detail-page");
  container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                    <img src="${product.image}" alt="${product.name}" class="w-full rounded-lg shadow-lg">
                </div>
                <div>
                    <h1 class="text-5xl font-teko text-secondary">${product.name}</h1>
                    <div class="flex items-center my-4">
                        <div class="rating mr-4">${renderStars(product.rating)}</div>
                        <span class="text-gray-600">${product.reviews.length} avaliações</span>
                    </div>
                    <p class="text-3xl font-bold text-primary mb-4">R$ ${product.price.toFixed(2)}</p>
                    <p class="text-gray-700 leading-relaxed mb-6">${product.description}</p>
                    <div class="flex items-center space-x-4">
                        <button class="add-to-cart-btn btn btn-primary flex-grow text-lg" data-id="${product.id}">Adicionar ao Carrinho</button>
                        <button class="wishlist-toggle p-3 rounded-lg border-2 border-gray-300 hover:border-primary ${wishlistedClass}" data-id="${product.id}">
                            <i class="fas fa-heart text-2xl"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Seção de Avaliações -->
            <div class="mt-12 bg-white p-8 rounded-lg shadow-md">
                <h2 class="text-4xl font-teko text-secondary mb-6">Avaliações de Clientes</h2>
                <div id="reviews-list" class="space-y-6 mb-8">
                    ${
                      product.reviews
                        .map(
                          (review) => `
                        <div class="border-b pb-4">
                            <div class="flex items-center mb-1">
                                <div class="rating mr-3">${renderStars(review.rating)}</div>
                                <p class="font-bold">${review.author}</p>
                            </div>
                            <p class="text-gray-600">${review.text}</p>
                        </div>
                    `,
                        )
                        .join("") ||
                      "<p>Este produto ainda não tem avaliações. Seja o primeiro a avaliar!</p>"
                    }
                </div>

                <!-- Formulário de Nova Avaliação -->
                <h3 class="text-3xl font-teko text-secondary mb-4">Deixe sua avaliação</h3>
                <form id="review-form" data-id="${product.id}">
                    <div class="mb-4">
                        <label for="author-name" class="block mb-1 font-semibold">Seu Nome</label>
                        <input type="text" id="author-name" class="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary" required>
                    </div>
                    <div class="mb-4">
                        <label class="block mb-1 font-semibold">Sua Nota</label>
                        <div id="new-review-rating" class="rating text-3xl cursor-pointer">
                            ${renderStars(0, true)}
                        </div>
                        <input type="hidden" id="rating-value" value="0" required>
                    </div>
                     <div class="mb-4">
                        <label for="review-text" class="block mb-1 font-semibold">Seu Comentário</label>
                        <textarea id="review-text" rows="4" class="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary" required></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Enviar Avaliação</button>
                </form>
            </div>
        `;
  addReviewFormListeners();
}

// Renderiza itens na wishlist
function renderWishlist() {
  const container = document.getElementById("wishlist-items");
  if (wishlistItems.length === 0) {
    container.innerHTML =
      '<p class="text-center text-gray-500">Sua lista de desejos está vazia.</p>';
    return;
  }
  container.innerHTML = wishlistItems
    .map((itemId) => {
      const product = products.find((p) => p.id === itemId);
      return `
                <div class="flex items-center bg-white p-4 rounded-lg shadow-md">
                    <img src="${product.image}" alt="${product.name}" class="w-20 h-20 object-cover rounded mr-4">
                    <div class="flex-grow">
                        <h3 class="text-xl font-teko">${product.name}</h3>
                        <p class="text-lg font-bold text-primary">R$ ${product.price.toFixed(2)}</p>
                    </div>
                    <div class="flex items-center space-x-4">
                         <button class="add-to-cart-btn btn btn-secondary btn-sm" data-id="${product.id}">Mover para Carrinho</button>
                         <button class="remove-from-wishlist text-gray-400 hover:text-red-500" data-id="${product.id}"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            `;
    })
    .join("");
}

// Renderiza itens no carrinho de compras
function renderCart() {
  const container = document.getElementById("cart-items");
  const totalEl = document.getElementById("cart-total");
  let total = 0;

  if (cartItems.length === 0) {
    container.innerHTML =
      '<p class="text-center text-gray-500">Seu carrinho está vazio.</p>';
    totalEl.textContent = "R$ 0,00";
    return;
  }

  container.innerHTML = cartItems
    .map((item) => {
      const product = products.find((p) => p.id === item.id);
      total += product.price * item.quantity;
      return `
                <div class="flex items-center">
                    <img src="${product.image}" alt="${product.name}" class="w-16 h-16 object-cover rounded mr-4">
                    <div class="flex-grow">
                        <h4 class="font-bold">${product.name}</h4>
                        <p>R$ ${product.price.toFixed(2)}</p>
                    </div>
                    <div class="flex items-center">
                        <input type="number" min="1" value="${item.quantity}" class="w-16 p-1 border rounded text-center cart-quantity-input" data-id="${product.id}">
                    </div>
                    <p class="w-24 text-right font-semibold">R$ ${(product.price * item.quantity).toFixed(2)}</p>
                    <button class="remove-from-cart ml-4 text-gray-400 hover:text-red-500" data-id="${product.id}"><i class="fas fa-times-circle"></i></button>
                </div>
            `;
    })
    .join("");

  totalEl.textContent = `R$ ${total.toFixed(2)}`;
}

// Renderiza avaliações em destaque na home
function renderFeaturedReviews() {
  const container = document.getElementById("featured-reviews");
  if (!container) return;

  const allReviews = products.flatMap((p) =>
    p.reviews.map((r) => ({ ...r, productName: p.name })),
  );
  const featured = allReviews.filter((r) => r.rating === 5).slice(0, 3);

  if (featured.length === 0) {
    container.innerHTML =
      '<p class="text-center text-gray-500 col-span-3">Ainda não temos avaliações em destaque.</p>';
    return;
  }

  container.innerHTML = featured
    .map(
      (review) => `
            <div class="bg-yellow-50 p-6 rounded-lg text-center flex flex-col items-center">
                <i class="fas fa-quote-left text-3xl text-accent mb-4"></i>
                <p class="text-gray-600 italic mb-4">"${review.text}"</p>
                <div class="rating text-accent mb-2">
                    ${renderStars(review.rating)}
                </div>
                <p class="font-bold text-secondary">${review.author}</p>
                <p class="text-sm text-gray-500">Sobre: ${review.productName}</p>
            </div>
        `,
    )
    .join("");
}

// ======================================================
// LÓGICA DA APLICAÇÃO
// ======================================================

// Navegação entre páginas
function showPage(pageId) {
  pages.forEach((page) => {
    page.classList.remove("active-page");
  });
  const newPage = document.getElementById(pageId + "-page");
  if (newPage) {
    newPage.classList.add("active-page");
  }
  window.scrollTo(0, 0);
}

// Atualiza os contadores no cabeçalho
function updateCounters() {
  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
  const wishlistCount = wishlistItems.length;

  cartCountEl.textContent = cartCount;
  wishlistCountEl.textContent = wishlistCount;

  // Atualizar mini contadores no menu lateral
  const wishlistMiniCount = document.getElementById("wishlist-mini-count");
  const cartMiniCount = document.getElementById("cart-mini-count");

  if (wishlistMiniCount) {
    wishlistMiniCount.textContent = wishlistCount;
  }
  if (cartMiniCount) {
    cartMiniCount.textContent = cartCount;
  }
}

// Adiciona um item ao carrinho
function addToCart(productId, productName) {
  fetch(`/cart/add/${productId}/`, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCSRFToken(),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        cartItems.push({ id: productId, quantity: 1 });
        updateCounters();
        showFeedback("Sucesso!", `${productName} foi adicionado ao carrinho.`);
      } else {
        showFeedback("Erro", "Não foi possível adicionar o produto.");
      }
    })
    .catch((error) => {
      console.error("Erro ao adicionar ao carrinho:", error);
      showFeedback("Erro", "Falha ao conectar com o servidor.");
    });
}

function getCSRFToken() {
  const cookieValue = document.cookie.match(
    "(^|;)\\s*csrftoken\\s*=\\s*([^;]+)",
  );
  return cookieValue ? cookieValue.pop() : "";
}

// Alterna item na wishlist
function toggleWishlist(productId) {
  const index = wishlistItems.indexOf(productId);
  if (index > -1) {
    wishlistItems.splice(index, 1);
    showFeedback(
      "Item removido",
      "O item foi removido da sua lista de desejos.",
    );
  } else {
    wishlistItems.push(productId);
    showFeedback(
      "Item adicionado!",
      "O item foi salvo na sua lista de desejos.",
    );
  }
  updateCounters();
  // Re-renderiza a view atual para atualizar o ícone de coração
  const activePageId = document.querySelector(".active-page").id;
  if (activePageId === "home-page" || activePageId === "products-page") {
    populateProducts();
  } else if (activePageId === "product-detail-page") {
    // Tenta re-renderizar o detalhe do produto se ele estiver ativo
    // O productId aqui pode não ser o mesmo se o usuário clicou em outro produto
    const detailPage = document.getElementById("product-detail-page");
    if (detailPage && detailPage.classList.contains("active-page")) {
      renderProductDetail(productId);
    }
  } else if (activePageId === "wishlist-page") {
    renderWishlist();
  }
}

// Modal de feedback
function showFeedback(title, message) {
  const modal = document.getElementById("feedback-modal");
  if (!modal) {
    console.error("Elemento #feedback-modal não encontrado!");
    return;
  }
  const modalTitleEl = document.getElementById("modal-title");
  const modalMessageEl = document.getElementById("modal-message");
  if (!modalTitleEl || !modalMessageEl) {
    console.error("Elementos internos do modal não encontrados!");
    return;
  }
  modalTitleEl.textContent = title;
  modalMessageEl.textContent = message;
  modal.classList.remove("hidden");
}

// Controle do menu lateral
function toggleMenu() {
  console.log("Toggle menu chamado");
  console.log("sideMenu exists:", !!sideMenu);
  console.log("menuOverlay exists:", !!menuOverlay);

  if (sideMenu && menuOverlay) {
    console.log(
      "Menu state before toggle:",
      sideMenu.classList.contains("open"),
    );
    sideMenu.classList.toggle("open");
    menuOverlay.classList.toggle("hidden");
    console.log(
      "Menu state after toggle:",
      sideMenu.classList.contains("open"),
    );

    // Adicionar/remover classe no body para prevenir scroll
    document.body.classList.toggle("menu-open");

    // Fechar subcategorias quando menu fecha
    if (!sideMenu.classList.contains("open")) {
      closeAllSubcategories();
    }
  } else {
    console.error("Elementos do menu não encontrados!");
    console.log("sideMenu:", sideMenu);
    console.log("menuOverlay:", menuOverlay);
  }
}

// Função para fechar todas as subcategorias
function closeAllSubcategories() {
  document.querySelectorAll(".subcategory-list").forEach((list) => {
    list.classList.remove("show");
    list.classList.add("hidden");
  });
  document.querySelectorAll(".category-toggle").forEach((btn) => {
    btn.classList.remove("active");
  });
}

// Controle do Carrossel Aprimorado
function updateCarousel() {
  try {
    if (!carouselItems.length || isCarouselTransitioning) {
      if (isCarouselTransitioning) {
        console.warn("⚠️ Carrossel em transição, ignorando atualização");
      } else {
        console.warn("⚠️ Nenhum slide encontrado no carrossel");
      }
      return;
    }

    isCarouselTransitioning = true;

    // Validar currentSlide
    const oldSlide = currentSlide;
    currentSlide = Math.max(0, Math.min(currentSlide, totalSlides - 1));

    if (oldSlide !== currentSlide) {
      console.warn(`🎠 Slide corrigido de ${oldSlide} para ${currentSlide}`);
    }

    // Use requestAnimationFrame para performance
    requestAnimationFrame(() => {
      try {
        // Atualizar slides
        carouselItems.forEach((item, index) => {
          if (!item) {
            console.error(`❌ Slide ${index} é null ou undefined`);
            return;
          }

          const isActive = index === currentSlide;
          const isPrev = index < currentSlide;

          item.classList.toggle("active", isActive);
          item.classList.toggle("prev", isPrev && !isActive);

          // Otimização: só remover classes se necessário
          if (!isActive && !isPrev) {
            item.classList.remove("active", "prev");
          }
        });

        // Atualizar indicadores
        if (carouselIndicators.length) {
          carouselIndicators.forEach((indicator, index) => {
            if (!indicator) {
              console.error(`❌ Indicador ${index} é null ou undefined`);
              return;
            }
            indicator.classList.toggle("active", index === currentSlide);
          });
        }

        // Resetar e iniciar barra de progresso
        updateProgressBar();

        // Liberar transição após 600ms (duração da animação CSS)
        setTimeout(() => {
          isCarouselTransitioning = false;
        }, 600);

        console.log(`🎠 Slide atual: ${currentSlide + 1}/${totalSlides}`);
      } catch (animationError) {
        console.error("❌ Erro na animação do carrossel:", animationError);
        isCarouselTransitioning = false;
      }
    });
  } catch (error) {
    console.error("❌ Erro crítico no updateCarousel:", error);
    isCarouselTransitioning = false;
  }
}

function updateProgressBar() {
  try {
    if (!carouselProgress) {
      console.warn("⚠️ Elemento carouselProgress não encontrado");
      return;
    }

    carouselProgress.style.width = "0%";
    carouselProgress.style.animation = "none";

    // Force reflow de forma otimizada
    void carouselProgress.offsetHeight;

    setTimeout(() => {
      if (!isCarouselPaused && carouselProgress && !document.hidden) {
        carouselProgress.style.animation = "progressBar 5s linear";
        console.log("📊 Barra de progresso atualizada");
      }
    }, 50);
  } catch (error) {
    console.error("❌ Erro ao atualizar barra de progresso:", error);
  }
}

function debounceCarouselAction(action, delay = 300) {
  if (carouselDebounceTimer) {
    clearTimeout(carouselDebounceTimer);
  }

  carouselDebounceTimer = setTimeout(() => {
    action();
    carouselDebounceTimer = null;
  }, delay);
}

function nextSlide() {
  try {
    if (totalSlides === 0 || isCarouselTransitioning) {
      console.warn(
        "⚠️ NextSlide bloqueado - slides:",
        totalSlides,
        "transitioning:",
        isCarouselTransitioning,
      );
      return;
    }
    const oldSlide = currentSlide;
    currentSlide = (currentSlide + 1) % totalSlides;
    console.log(`➡️ Próximo slide: ${oldSlide} → ${currentSlide}`);
    updateCarousel();
  } catch (error) {
    console.error("❌ Erro em nextSlide:", error);
  }
}

function prevSlide() {
  try {
    if (totalSlides === 0 || isCarouselTransitioning) {
      console.warn(
        "⚠️ PrevSlide bloqueado - slides:",
        totalSlides,
        "transitioning:",
        isCarouselTransitioning,
      );
      return;
    }
    const oldSlide = currentSlide;
    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    console.log(`⬅️ Slide anterior: ${oldSlide} → ${currentSlide}`);
    updateCarousel();
  } catch (error) {
    console.error("❌ Erro em prevSlide:", error);
  }
}

function goToSlide(slideIndex) {
  try {
    if (
      totalSlides === 0 ||
      slideIndex < 0 ||
      slideIndex >= totalSlides ||
      isCarouselTransitioning
    ) {
      console.warn("⚠️ GoToSlide bloqueado:", {
        slideIndex,
        totalSlides,
        isCarouselTransitioning,
      });
      return;
    }
    if (slideIndex === currentSlide) {
      console.log("ℹ️ Já no slide", slideIndex);
      return; // Não fazer nada se já estiver no slide
    }
    const oldSlide = currentSlide;
    currentSlide = slideIndex;
    console.log(`🎯 Ir para slide: ${oldSlide} → ${currentSlide}`);
    updateCarousel();
  } catch (error) {
    console.error("❌ Erro em goToSlide:", error);
  }
}

function startCarouselAutoplay() {
  try {
    if (totalSlides <= 1) {
      console.warn(
        "⚠️ Auto-play não iniciado - slides insuficientes:",
        totalSlides,
      );
      return;
    }

    stopCarouselAutoplay(); // Limpar interval anterior
    carouselInterval = setInterval(() => {
      try {
        if (!isCarouselPaused && !document.hidden && document.hasFocus()) {
          nextSlide();
        }
      } catch (error) {
        console.error("❌ Erro no auto-play interval:", error);
        stopCarouselAutoplay();
      }
    }, 5000);
    console.log("▶️ Auto-play do carrossel iniciado");
  } catch (error) {
    console.error("❌ Erro ao iniciar auto-play:", error);
  }
}

function stopCarouselAutoplay() {
  try {
    if (carouselInterval) {
      clearInterval(carouselInterval);
      carouselInterval = null;
      console.log("⏹️ Auto-play do carrossel parado");
    }
  } catch (error) {
    console.error("❌ Erro ao parar auto-play:", error);
  }
}

function pauseCarousel() {
  isCarouselPaused = true;
  if (carouselProgress) {
    carouselProgress.style.animationPlayState = "paused";
  }
  console.log("⏸️ Carrossel pausado");
}

function resumeCarousel() {
  isCarouselPaused = false;
  if (carouselProgress && !document.hidden) {
    carouselProgress.style.animationPlayState = "running";
  }
  console.log("▶️ Carrossel retomado");
}

function isCarouselInView() {
  if (!carouselContainer) return false;
  const rect = carouselContainer.getBoundingClientRect();
  return rect.top < window.innerHeight && rect.bottom > 0;
}

function resetCarouselAutoplay() {
  stopCarouselAutoplay();
  startCarouselAutoplay();
}

// ======================================================
// INICIALIZAÇÃO E EVENT LISTENERS
// ======================================================

// Preenche as seções de produtos com base no filtro
function populateProducts(filter = "all", searchTerm = "") {
  const featuredContainer = document.getElementById("featured-products");
  const recommendedContainer = document.getElementById("recommended-products");
  const productListContainer = document.getElementById("product-list");

  let filteredProducts = products;

  // Filtro por categoria
  if (filter !== "all") {
    filteredProducts = filteredProducts.filter((p) => p.category === filter);
  }

  // Filtro por busca
  if (searchTerm) {
    filteredProducts = filteredProducts.filter((p) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()),
    );
  }

  const productHtml = filteredProducts.map(createProductCard).join("");

  // Na página de produtos, mostra o resultado filtrado
  if (
    document.getElementById("products-page").classList.contains("active-page")
  ) {
    productListContainer.innerHTML =
      productHtml || "<p>Nenhum produto encontrado.</p>";
  }

  // Na home, continua mostrando os fixos
  if (featuredContainer) {
    featuredContainer.innerHTML = products
      .slice(0, 4)
      .map(createProductCard)
      .join("");
  }
  if (recommendedContainer) {
    recommendedContainer.innerHTML = products
      .slice(-4)
      .map(createProductCard)
      .join("");
  }
}

// Listeners para o formulário de avaliação
function addReviewFormListeners() {
  const reviewForm = document.getElementById("review-form");
  if (reviewForm) {
    reviewForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const productId = parseInt(reviewForm.dataset.id);
      const product = products.find((p) => p.id === productId);
      const author = document.getElementById("author-name").value;
      const text = document.getElementById("review-text").value;
      const rating = parseInt(document.getElementById("rating-value").value);

      if (rating === 0) {
        alert("Por favor, selecione uma nota.");
        return;
      }

      product.reviews.push({ author, text, rating });

      // Recalcula a média de rating do produto
      const totalRating = product.reviews.reduce((sum, r) => sum + r.rating, 0);
      product.rating = totalRating / product.reviews.length;

      showFeedback("Obrigado!", "Sua avaliação foi enviada com sucesso.");
      renderProductDetail(productId); // Re-renderiza a página para mostrar a nova avaliação
    });

    const stars = document.querySelectorAll("#new-review-rating .fa-star");
    stars.forEach((star) => {
      star.addEventListener("click", () => {
        const value = parseInt(star.dataset.value);
        document.getElementById("rating-value").value = value;
        stars.forEach((s) => {
          s.classList.toggle("text-accent", parseInt(s.dataset.value) <= value);
        });
      });
    });
  }
}

// Delegação de eventos no corpo do documento
document.body.addEventListener("click", (e) => {
  const addToCartBtn = e.target.closest(".add-to-cart-btn");
  if (addToCartBtn) {
    const productId = parseInt(addToCartBtn.dataset.id);
    const productName = addToCartBtn.dataset.productName; // Obter o nome do produto
    addToCart(productId, productName);
    const wishlistIndex = wishlistItems.indexOf(productId);
    if (wishlistIndex > -1) {
      toggleWishlist(productId);
    }
  }

  const productLink = e.target.closest(".product-link");
  if (productLink) {
    const productId = parseInt(productLink.dataset.id);
    renderProductDetail(productId);
    showPage("product-detail");
  }

  const wishlistToggle = e.target.closest(".wishlist-toggle");
  if (wishlistToggle) {
    const productId = parseInt(wishlistToggle.dataset.id);
    toggleWishlist(productId);
  }

  const removeFromWishlistBtn = e.target.closest(".remove-from-wishlist");
  if (removeFromWishlistBtn) {
    const productId = parseInt(removeFromWishlistBtn.dataset.id);
    toggleWishlist(productId);
  }

  const removeFromCartBtn = e.target.closest(".remove-from-cart");
  if (removeFromCartBtn) {
    const productId = parseInt(removeFromCartBtn.dataset.id);
    cartItems = cartItems.filter((item) => item.id !== productId);
    renderCart();
    updateCounters();
  }
});

// Event listener para navegação principal
navLinks.forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const pageId = link.dataset.page;
    showPage(pageId);
    if (sideMenu.classList.contains("open")) {
      toggleMenu();
    }
  });
});

// Event listener para abrir a wishlist e o carrinho
if (wishlistBtn) {
  wishlistBtn.addEventListener("click", () => {
    renderWishlist();
    showPage("wishlist");
  });
}
if (cartBtn) {
  cartBtn.addEventListener("click", () => {
    renderCart();
    showPage("checkout");
  });
}

// Listeners do menu lateral
console.log("Configurando listeners do menu...");
console.log("openMenuBtn exists:", !!openMenuBtn);

if (openMenuBtn) {
  console.log("Adicionando listener ao botão de abrir menu");
  openMenuBtn.addEventListener("click", (e) => {
    e.preventDefault();
    console.log("Botão abrir menu clicado");
    toggleMenu();
  });
} else {
  console.error("Botão de abrir menu não encontrado!");
}

if (closeMenuBtn) {
  console.log("Adicionando listener ao botão de fechar menu");
  closeMenuBtn.addEventListener("click", (e) => {
    e.preventDefault();
    console.log("Botão fechar menu clicado");
    toggleMenu();
  });
} else {
  console.error("Botão de fechar menu não encontrado!");
}

if (menuOverlay) {
  console.log("Adicionando listener ao overlay");
  menuOverlay.addEventListener("click", (e) => {
    e.preventDefault();
    console.log("Overlay clicado");
    toggleMenu();
  });
} else {
  console.error("Menu overlay não encontrado!");
}

// Fechar menu com tecla ESC
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && sideMenu && sideMenu.classList.contains("open")) {
    toggleMenu();
  }
});

// Listeners para subcategorias
document.querySelectorAll(".category-toggle").forEach((toggle) => {
  toggle.addEventListener("click", function (e) {
    e.preventDefault();
    console.log("Subcategoria clicada:", this.textContent);

    const subcategoryList =
      this.parentElement.querySelector(".subcategory-list");
    if (!subcategoryList) return;

    const isOpen = subcategoryList.classList.contains("show");

    // Fecha todas as outras subcategorias
    document.querySelectorAll(".subcategory-list").forEach((list) => {
      if (list !== subcategoryList) {
        list.classList.remove("show");
        list.classList.add("hidden");
      }
    });
    document.querySelectorAll(".category-toggle").forEach((btn) => {
      if (btn !== this) {
        btn.classList.remove("active");
      }
    });

    // Alterna a subcategoria atual
    if (!isOpen) {
      subcategoryList.classList.remove("hidden");
      subcategoryList.classList.add("show");
      this.classList.add("active");
    } else {
      subcategoryList.classList.remove("show");
      subcategoryList.classList.add("hidden");
      this.classList.remove("active");
    }
  });
});

// Listener da busca
const searchInput = document.getElementById("search-input");
if (searchInput) {
  searchInput.addEventListener("keyup", (e) => {
    const searchTerm = e.target.value.toLowerCase();

    // Se há termo de busca, filtra produtos
    if (searchTerm) {
      showPage("products");
      document.getElementById("product-list").innerHTML = products
        .map(createProductCard)
        .join(""); // Reset view before filtering
      populateProducts("all", searchTerm);

      // Filtrar categorias visíveis baseado na busca
      filterCategoriesInMenu(searchTerm);

      // Mostrar contador de resultados
      updateSearchCounter(searchTerm);

      // Mostrar botão de limpar filtros
      document.getElementById("reset-filters-btn").classList.remove("hidden");
    } else {
      // Se não há busca, mostra todas as categorias
      showAllCategoriesInMenu();
      hideSearchCounter();
      document.getElementById("reset-filters-btn").classList.add("hidden");
    }
  });
}

// Listener das categorias
document.querySelectorAll(".category-link").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const category = e.target.dataset.category;
    showPage("products");
    document.getElementById("product-list").innerHTML = products
      .map(createProductCard)
      .join(""); // Reset view before filtering
    populateProducts(category);
    toggleMenu();
  });
});

// Listener para o formulário de checkout
const checkoutForm = document.getElementById("checkout-form");
if (checkoutForm) {
  checkoutForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (cartItems.length === 0) {
      showFeedback(
        "Carrinho Vazio",
        "Adicione itens ao carrinho antes de finalizar a compra.",
      );
      return;
    }
    showFeedback(
      "Pedido Confirmado!",
      "Obrigado por sua compra. Seu pedido foi processado com sucesso.",
    );
    cartItems = [];
    updateCounters();
    renderCart();
    e.target.reset();
    setTimeout(() => showPage("home"), 2000);
  });
}

// Listener do formulário de contato
const contactForm = document.getElementById("contact-form");
if (contactForm) {
  contactForm.addEventListener("submit", (e) => {
    e.preventDefault();
    showFeedback(
      "Mensagem Enviada!",
      "Obrigado por entrar em contato. Responderemos em breve.",
    );
    e.target.reset();
  });
}

// Listener para quantidade no carrinho
const cartItemsContainer = document.getElementById("cart-items");
if (cartItemsContainer) {
  cartItemsContainer.addEventListener("change", (e) => {
    if (e.target.classList.contains("cart-quantity-input")) {
      const productId = parseInt(e.target.dataset.id);
      const newQuantity = parseInt(e.target.value);
      const item = cartItems.find((i) => i.id === productId);
      if (item && newQuantity > 0) {
        item.quantity = newQuantity;
      } else {
        cartItems = cartItems.filter((i) => i.id !== productId);
      }
      renderCart();
      updateCounters();
    }
  });
}

// Fechar modal
const modalCloseBtn = document.getElementById("modal-close-btn");
if (modalCloseBtn) {
  modalCloseBtn.addEventListener("click", () => {
    document.getElementById("feedback-modal").classList.add("hidden");
  });
}

// ======================================================
// CARROSSEL - EVENT LISTENERS
// ======================================================

function setupCarouselListeners() {
  try {
    // Botões de navegação com debounce
    if (nextBtn) {
      nextBtn.addEventListener("click", (e) => {
        try {
          e.preventDefault();
          console.log("🖱️ Botão next clicado");
          debounceCarouselAction(() => {
            nextSlide();
            resetCarouselAutoplay();
          }, 200);
        } catch (error) {
          console.error("❌ Erro no click do nextBtn:", error);
        }
      });
    } else {
      console.warn("⚠️ Botão next não encontrado");
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", (e) => {
        try {
          e.preventDefault();
          console.log("🖱️ Botão prev clicado");
          debounceCarouselAction(() => {
            prevSlide();
            resetCarouselAutoplay();
          }, 200);
        } catch (error) {
          console.error("❌ Erro no click do prevBtn:", error);
        }
      });
    } else {
      console.warn("⚠️ Botão prev não encontrado");
    }

    // Indicadores com debounce
    if (carouselIndicators.length > 0) {
      carouselIndicators.forEach((indicator, index) => {
        if (!indicator) {
          console.error(`❌ Indicador ${index} é null`);
          return;
        }
        indicator.addEventListener("click", (e) => {
          try {
            e.preventDefault();
            console.log(`🖱️ Indicador ${index} clicado`);
            debounceCarouselAction(() => {
              goToSlide(index);
              resetCarouselAutoplay();
            }, 150);
          } catch (error) {
            console.error(`❌ Erro no click do indicador ${index}:`, error);
          }
        });
      });
    } else {
      console.warn("⚠️ Nenhum indicador encontrado");
    }

    // Hover para pausar/retomar
    if (carouselContainer) {
      carouselContainer.addEventListener("mouseenter", () => {
        try {
          console.log("🖱️ Mouse enter - pausando carrossel");
          pauseCarousel();
        } catch (error) {
          console.error("❌ Erro no mouseenter:", error);
        }
      });

      carouselContainer.addEventListener("mouseleave", () => {
        try {
          console.log("🖱️ Mouse leave - retomando carrossel");
          resumeCarousel();
        } catch (error) {
          console.error("❌ Erro no mouseleave:", error);
        }
      });

      // Suporte para toque
      carouselContainer.addEventListener(
        "touchstart",
        (e) => {
          try {
            if (e.changedTouches && e.changedTouches[0]) {
              touchStartX = e.changedTouches[0].screenX;
              console.log("👆 Touch start:", touchStartX);
            }
          } catch (error) {
            console.error("❌ Erro no touchstart:", error);
          }
        },
        { passive: true },
      );

      carouselContainer.addEventListener(
        "touchend",
        (e) => {
          try {
            if (e.changedTouches && e.changedTouches[0]) {
              touchEndX = e.changedTouches[0].screenX;
              console.log("👆 Touch end:", touchEndX);
              handleSwipe();
            }
          } catch (error) {
            console.error("❌ Erro no touchend:", error);
          }
        },
        { passive: true },
      );
    } else {
      console.warn(
        "⚠️ Container do carrossel não encontrado para eventos de hover/touch",
      );
    }

    // Suporte para teclado (apenas quando carrossel está visível)
    document.addEventListener("keydown", (e) => {
      try {
        if (!carouselContainer) return;

        const isCarouselVisible = carouselContainer.offsetParent !== null;
        if (!isCarouselVisible) return;

        if (e.key === "ArrowLeft") {
          e.preventDefault();
          console.log("⌨️ Seta esquerda pressionada");
          debounceCarouselAction(() => {
            prevSlide();
            resetCarouselAutoplay();
          }, 100);
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          console.log("⌨️ Seta direita pressionada");
          debounceCarouselAction(() => {
            nextSlide();
            resetCarouselAutoplay();
          }, 100);
        }
      } catch (error) {
        console.error("❌ Erro no keydown:", error);
      }
    });

    // Pausar quando a página não está visível
    document.addEventListener("visibilitychange", () => {
      try {
        if (document.hidden) {
          console.log("👁️ Página oculta - pausando carrossel");
          pauseCarousel();
          stopCarouselAutoplay();
        } else if (isCarouselInView()) {
          console.log("👁️ Página visível - retomando carrossel");
          resumeCarousel();
          startCarouselAutoplay();
        }
      } catch (error) {
        console.error("❌ Erro no visibilitychange:", error);
      }
    });

    // Pausar quando a janela perde o foco
    window.addEventListener("blur", () => {
      try {
        console.log("🎯 Janela perdeu foco - pausando carrossel");
        pauseCarousel();
      } catch (error) {
        console.error("❌ Erro no blur:", error);
      }
    });

    window.addEventListener("focus", () => {
      try {
        if (!document.hidden && isCarouselInView()) {
          console.log("🎯 Janela ganhou foco - retomando carrossel");
          resumeCarousel();
        }
      } catch (error) {
        console.error("❌ Erro no focus:", error);
      }
    });

    // Pausar carrossel quando não está visível (Intersection Observer)
    if ("IntersectionObserver" in window && carouselContainer) {
      try {
        const observer = new IntersectionObserver(
          (entries) => {
            try {
              entries.forEach((entry) => {
                if (entry.isIntersecting) {
                  console.log("👀 Carrossel visível - iniciando auto-play");
                  if (!isCarouselPaused && !document.hidden) {
                    startCarouselAutoplay();
                  }
                } else {
                  console.log("👀 Carrossel invisível - parando auto-play");
                  stopCarouselAutoplay();
                }
              });
            } catch (error) {
              console.error("❌ Erro no IntersectionObserver callback:", error);
            }
          },
          { threshold: 0.5 },
        );

        observer.observe(carouselContainer);
        console.log("👀 IntersectionObserver configurado");
      } catch (error) {
        console.error("❌ Erro ao configurar IntersectionObserver:", error);
      }
    } else {
      console.warn(
        "⚠️ IntersectionObserver não suportado ou container não encontrado",
      );
    }

    console.log("🎛️ Listeners do carrossel configurados com sucesso");
  } catch (error) {
    console.error(
      "❌ Erro crítico ao configurar listeners do carrossel:",
      error,
    );
  }
}

function handleSwipe() {
  try {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;
    const absDiff = Math.abs(diff);

    console.log(
      `👆 Swipe detectado: ${touchStartX} → ${touchEndX} (diff: ${diff})`,
    );

    if (absDiff > swipeThreshold) {
      // Prevenir swipes muito rápidos ou acidentais
      if (absDiff > 300) {
        console.warn("⚠️ Swipe muito rápido, ignorando");
        return;
      }

      debounceCarouselAction(() => {
        if (diff > 0) {
          // Swipe left - next slide
          nextSlide();
          console.log("👆 Swipe esquerdo - próximo slide");
        } else {
          // Swipe right - previous slide
          prevSlide();
          console.log("👆 Swipe direito - slide anterior");
        }
        resetCarouselAutoplay();
      }, 100);
    } else {
      console.log("👆 Swipe insuficiente, ignorando");
    }
  } catch (error) {
    console.error("❌ Erro no handleSwipe:", error);
  } finally {
    // Reset touch positions
    touchStartX = 0;
    touchEndX = 0;
  }
}

// Inicialização
function init() {
  console.log("Inicializando India Oasis...");

  // Verificar se elementos do menu existem
  console.log("Elementos do menu:", {
    sideMenu: !!sideMenu,
    menuOverlay: !!menuOverlay,
    openMenuBtn: !!openMenuBtn,
    closeMenuBtn: !!closeMenuBtn,
  });

  const productListContainer = document.getElementById("product-list");
  if (productListContainer) {
    productListContainer.innerHTML = products.map(createProductCard).join("");
  }

  populateProducts();
  renderFeaturedReviews();
  updateCounters();
  showPage("home");

  // Inicializar carrossel aprimorado
  try {
    if (totalSlides > 0) {
      console.log(`🎠 Inicializando carrossel com ${totalSlides} slides`);
      setupCarouselListeners();
      updateCarousel();

      // Delay para garantir que o DOM esteja completamente carregado
      setTimeout(() => {
        startCarouselAutoplay();
      }, 100);

      console.log("🎠 Carrossel inicializado com sucesso");
    } else {
      console.warn("⚠️ Carrossel não inicializado - nenhum slide encontrado");
    }
  } catch (error) {
    console.error("❌ Erro crítico na inicialização do carrossel:", error);
  }

  // Adicionar funcionalidade de demonstração
  setupDemoFeatures();

  console.log("Menu lateral inicializado com", products.length, "produtos");
  console.log(
    "Funcionalidades ativas: busca, categorias expandíveis, contadores",
  );
}

// Configurar recursos de demonstração
function setupDemoFeatures() {
  // Adicionar indicador visual para o botão do menu
  if (openMenuBtn) {
    openMenuBtn.style.position = "relative";

    // Criar tooltip
    const tooltip = document.createElement("div");
    tooltip.className = "demo-tooltip";
    tooltip.textContent = "Clique para abrir o menu";
    tooltip.style.cssText = `
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s;
        z-index: 1000;
      `;

    openMenuBtn.appendChild(tooltip);

    // Mostrar tooltip no hover
    openMenuBtn.addEventListener("mouseenter", () => {
      tooltip.style.opacity = "1";
    });

    openMenuBtn.addEventListener("mouseleave", () => {
      tooltip.style.opacity = "0";
    });
  }

  // Adicionar animação de chamada de atenção
  setTimeout(() => {
    if (openMenuBtn) {
      openMenuBtn.style.animation = "pulse 2s infinite";
    }
  }, 2000);
}

// Função para filtrar categorias no menu baseado na busca
function filterCategoriesInMenu(searchTerm) {
  const categories = document.querySelectorAll(
    ".category-section, .category-link",
  );

  let visibleCategories = 0;
  categories.forEach((category) => {
    const categoryText = category.textContent.toLowerCase();
    const categoryItem = category.closest("li");

    if (categoryText.includes(searchTerm)) {
      categoryItem.style.display = "block";
      categoryItem.style.opacity = "1";
      visibleCategories++;
    } else {
      categoryItem.style.display = "none";
      categoryItem.style.opacity = "0.5";
    }
  });

  console.log(
    `Filtro aplicado: ${visibleCategories} categorias visíveis para "${searchTerm}"`,
  );
}

// Função para mostrar todas as categorias
function showAllCategoriesInMenu() {
  const categories = document.querySelectorAll(
    ".category-section, .category-link",
  );

  categories.forEach((category) => {
    const categoryItem = category.closest("li");
    categoryItem.style.display = "block";
    categoryItem.style.opacity = "1";
  });
}

// Função para destacar categoria ativa
function highlightActiveCategory(categoryName) {
  // Remove destaque anterior
  document.querySelectorAll(".category-active").forEach((el) => {
    el.classList.remove("category-active");
  });

  // Adiciona destaque à categoria atual
  const activeCategory = document.querySelector(
    `[data-category="${categoryName}"]`,
  );
  if (activeCategory) {
    activeCategory.classList.add("category-active");
  }
}

// Função para atualizar contador de busca
function updateSearchCounter(searchTerm) {
  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const counter = document.getElementById("search-results-counter");
  const countSpan = document.getElementById("results-count");

  countSpan.textContent = filteredProducts.length;
  counter.classList.remove("hidden");
}

// Função para esconder contador de busca
function hideSearchCounter() {
  const counter = document.getElementById("search-results-counter");
  counter.classList.add("hidden");
}

// Listener para botão de limpar filtros
const resetBtn = document.getElementById("reset-filters-btn");
if (resetBtn) {
  resetBtn.addEventListener("click", () => {
    // Limpar campo de busca
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
      searchInput.value = "";
    }

    // Mostrar todas as categorias
    showAllCategoriesInMenu();

    // Esconder contador e botão
    hideSearchCounter();
    resetBtn.classList.add("hidden");

    // Voltar para página inicial
    showPage("home");

    console.log("Filtros limpos, voltando à visualização padrão");

    // Notificação de filtros limpos
    if (window.actionFeedback) {
      window.actionFeedback.copied("Filtros limpos");
    }
  });
}

// ======================================================
// FUNCIONALIDADES AVANÇADAS
// ======================================================

// Verificar se desbloqueou frete grátis
function checkFreeShipping() {
  const total = cartItems.reduce((sum, item) => {
    const product = products.find((p) => p.id === item.id);
    return sum + (product ? product.price * item.quantity : 0);
  }, 0);

  const freeShippingThreshold = 150;

  if (total >= freeShippingThreshold && window.cartNotifications) {
    // Verificar se é a primeira vez que atinge o limite
    const wasUnderThreshold =
      localStorage.getItem("wasUnderFreeShipping") === "true";
    if (wasUnderThreshold) {
      window.cartNotifications.freeShippingUnlocked();
      localStorage.removeItem("wasUnderFreeShipping");
    }
  } else {
    localStorage.setItem("wasUnderFreeShipping", "true");
  }
}

// Atualizar ícones de wishlist
function updateWishlistIcons() {
  document
    .querySelectorAll('[data-action="add-to-wishlist"]')
    .forEach((btn) => {
      const productId = parseInt(btn.getAttribute("data-product-id"));
      const isInWishlist = wishlistItems.some((item) => item.id === productId);

      const icon = btn.querySelector("i");
      if (icon) {
        if (isInWishlist) {
          icon.className = "fas fa-heart text-red-500";
          btn.setAttribute("title", "Remover dos favoritos");
        } else {
          icon.className = "far fa-heart";
          btn.setAttribute("title", "Adicionar aos favoritos");
        }
      }
    });
}

// Simulação de alertas de preço
function simulatePriceAlert() {
  if (wishlistItems.length > 0 && window.wishlistNotifications) {
    const randomItem =
      wishlistItems[Math.floor(Math.random() * wishlistItems.length)];
    const product = products.find((p) => p.id === randomItem.id);

    if (product) {
      const oldPrice = product.price;
      const newPrice = product.price * 0.8; // 20% de desconto

      setTimeout(() => {
        window.wishlistNotifications.priceDropAlert(
          product.name,
          oldPrice,
          newPrice,
        );
      }, 10000); // Simular após 10 segundos
    }
  }
}

// Detectar erros de formulário
function setupFormValidation() {
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const requiredFields = form.querySelectorAll("[required]");
      let hasErrors = false;

      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          hasErrors = true;
          field.classList.add("border-red-500");
        } else {
          field.classList.remove("border-red-500");
        }
      });

      if (hasErrors) {
        e.preventDefault();
        if (window.actionFeedback) {
          window.actionFeedback.formError(
            "Por favor, preencha todos os campos obrigatórios",
          );
        }
      }
    });
  });
}

// Inicializar funcionalidades avançadas
function initAdvancedFeatures() {
  updateWishlistIcons();
  setupFormValidation();

  // Simular alerta de preço para demonstração
  if (window.location.pathname.includes("wishlist.html")) {
    simulatePriceAlert();
  }

  // Configurar indicador de progresso de scroll
  setupScrollProgress();

  // Configurar botão voltar ao topo
  setupBackToTop();
}

// Indicador de progresso de scroll
function setupScrollProgress() {
  const progressBar = document.createElement("div");
  progressBar.className = "scroll-indicator";
  progressBar.innerHTML = '<div class="scroll-progress"></div>';
  document.body.appendChild(progressBar);

  const progress = progressBar.querySelector(".scroll-progress");

  window.addEventListener("scroll", () => {
    const scrollTop = window.pageYOffset;
    const docHeight =
      document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = (scrollTop / docHeight) * 100;

    progress.style.width = scrollPercent + "%";
  });
}

// Botão voltar ao topo
function setupBackToTop() {
  const backToTop = document.createElement("button");
  backToTop.className = "back-to-top";
  backToTop.innerHTML = '<i class="fas fa-arrow-up"></i>';
  backToTop.title = "Voltar ao topo";
  document.body.appendChild(backToTop);

  window.addEventListener("scroll", () => {
    if (window.pageYOffset > 300) {
      backToTop.classList.add("show");
    } else {
      backToTop.classList.remove("show");
    }
  });

  backToTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

// Executa a inicialização quando o DOM estiver pronto
document.addEventListener("DOMContentLoaded", () => {
  // Assume que a variável global 'products' já está definida
  // Se 'products' for carregado assincronamente, este código precisará ser ajustado
  if (typeof products !== "undefined" && Array.isArray(products)) {
    init();
    // Inicializar funcionalidades avançadas após um pequeno delay para garantir que tudo esteja carregado
    setTimeout(initAdvancedFeatures, 500);
  } else {
    console.error(
      "Erro: A variável global 'products' não foi definida ou não é um array.",
    );
    // Tentar inicializar mesmo assim, caso 'products' seja preenchido posteriormente
    // ou se o init não depender diretamente de 'products' para elementos básicos
    init();
    setTimeout(initAdvancedFeatures, 500);
  }
});
