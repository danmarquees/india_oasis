// ===== SISTEMA DE NOTIFICAÇÕES TOAST =====
// Sistema global de notificações para India Oasis

class ToastSystem {
  constructor() {
    this.container = null;
    this.toasts = new Map();
    this.defaultDuration = 5000;
    this.init();
  }

  init() {
    // Criar container se não existir
    if (!document.querySelector(".toast-container")) {
      this.container = document.createElement("div");
      this.container.className = "toast-container";
      document.body.appendChild(this.container);
    } else {
      this.container = document.querySelector(".toast-container");
    }
  }

  show(options) {
    const {
      type = "info",
      title = "",
      message = "",
      duration = this.defaultDuration,
      persistent = false,
      actions = [],
    } = options;

    const toastId = this.generateId();
    const toast = this.createToast(
      toastId,
      type,
      title,
      message,
      persistent,
      actions,
    );

    this.container.appendChild(toast);
    this.toasts.set(toastId, { element: toast, timer: null });

    // Mostrar toast com animação
    requestAnimationFrame(() => {
      toast.classList.add("show");
    });

    // Auto-hide se não for persistente
    if (!persistent && duration > 0) {
      this.setAutoHide(toastId, duration);
    }

    return toastId;
  }

  createToast(id, type, title, message, persistent, actions) {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.setAttribute("data-toast-id", id);

    const icon = this.getIcon(type);

    toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${icon}"></i>
            </div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ""}
                <div class="toast-message">${message}</div>
                ${actions.length > 0 ? this.createActions(actions) : ""}
            </div>
            ${!persistent ? '<button class="toast-close" aria-label="Fechar">&times;</button>' : ""}
            ${!persistent ? '<div class="toast-progress"><div class="toast-progress-bar"></div></div>' : ""}
        `;

    // Event listeners
    if (!persistent) {
      const closeBtn = toast.querySelector(".toast-close");
      closeBtn.addEventListener("click", () => this.hide(id));
    }

    // Event listeners para ações
    actions.forEach((action, index) => {
      const actionBtn = toast.querySelector(`[data-action="${index}"]`);
      if (actionBtn) {
        actionBtn.addEventListener("click", (e) => {
          e.preventDefault();
          action.handler();
          if (action.autoClose !== false) {
            this.hide(id);
          }
        });
      }
    });

    return toast;
  }

  createActions(actions) {
    const actionsHtml = actions
      .map(
        (action, index) =>
          `<button class="toast-action btn btn-sm ${action.style || "btn-primary"}" data-action="${index}">
                ${action.icon ? `<i class="fas ${action.icon} mr-1"></i>` : ""}
                ${action.label}
            </button>`,
      )
      .join("");

    return `<div class="toast-actions mt-2 flex space-x-2">${actionsHtml}</div>`;
  }

  getIcon(type) {
    const icons = {
      success: "fa-check",
      error: "fa-times",
      warning: "fa-exclamation-triangle",
      info: "fa-info",
    };
    return icons[type] || icons.info;
  }

  setAutoHide(toastId, duration) {
    const toastData = this.toasts.get(toastId);
    if (!toastData) return;

    const progressBar = toastData.element.querySelector(".toast-progress-bar");
    if (progressBar) {
      progressBar.style.transitionDuration = `${duration}ms`;
      progressBar.style.transform = "translateX(0)";
    }

    toastData.timer = setTimeout(() => {
      this.hide(toastId);
    }, duration);
  }

  hide(toastId) {
    const toastData = this.toasts.get(toastId);
    if (!toastData) return;

    const toast = toastData.element;

    // Limpar timer se existir
    if (toastData.timer) {
      clearTimeout(toastData.timer);
    }

    // Animação de saída
    toast.classList.add("hiding");

    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      this.toasts.delete(toastId);
    }, 300);
  }

  hideAll() {
    this.toasts.forEach((_, toastId) => {
      this.hide(toastId);
    });
  }

  generateId() {
    return (
      "toast-" + Date.now() + "-" + Math.random().toString(36).substr(2, 9)
    );
  }

  // Métodos de conveniência
  success(title, message, options = {}) {
    return this.show({ type: "success", title, message, ...options });
  }

  error(title, message, options = {}) {
    return this.show({ type: "error", title, message, ...options });
  }

  warning(title, message, options = {}) {
    return this.show({ type: "warning", title, message, ...options });
  }

  info(title, message, options = {}) {
    return this.show({ type: "info", title, message, ...options });
  }
}

// ===== SISTEMA DE CARRINHO COM NOTIFICAÇÕES =====
class CartNotifications {
  constructor(toastSystem) {
    this.toast = toastSystem;
  }

  itemAdded(productName, quantity = 1) {
    this.toast.success(
      "Produto Adicionado!",
      `${productName} foi adicionado ao carrinho`,
      {
        duration: 3000,
        actions: [
          {
            label: "Ver Carrinho",
            icon: "fa-shopping-cart",
            style: "btn-primary",
            handler: () => (window.location.href = "cart.html"),
          },
        ],
      },
    );
  }

  itemRemoved(productName) {
    this.toast.info(
      "Produto Removido",
      `${productName} foi removido do carrinho`,
      { duration: 2000 },
    );
  }

  quantityUpdated(productName, newQuantity) {
    this.toast.info(
      "Quantidade Atualizada",
      `${productName}: ${newQuantity} ${newQuantity === 1 ? "unidade" : "unidades"}`,
      { duration: 2000 },
    );
  }

  cartCleared() {
    this.toast.warning(
      "Carrinho Limpo",
      "Todos os itens foram removidos do carrinho",
      { duration: 2000 },
    );
  }

  freeShippingUnlocked() {
    this.toast.success(
      "Frete Grátis Liberado! 🎉",
      "Parabéns! Você ganhou frete grátis neste pedido",
      {
        duration: 5000,
        actions: [
          {
            label: "Finalizar Compra",
            icon: "fa-credit-card",
            style: "btn-primary",
            handler: () => document.getElementById("checkout-btn")?.click(),
          },
        ],
      },
    );
  }
}

// ===== SISTEMA DE WISHLIST COM NOTIFICAÇÕES =====
class WishlistNotifications {
  constructor(toastSystem) {
    this.toast = toastSystem;
  }

  itemAdded(productName) {
    this.toast.success(
      "Adicionado aos Favoritos! ❤️",
      `${productName} foi salvo na sua lista de desejos`,
      {
        duration: 3000,
        actions: [
          {
            label: "Ver Lista",
            icon: "fa-heart",
            style: "btn-primary",
            handler: () => (window.location.href = "wishlist.html"),
          },
        ],
      },
    );
  }

  itemRemoved(productName) {
    this.toast.info(
      "Removido dos Favoritos",
      `${productName} foi removido da sua lista`,
      { duration: 2000 },
    );
  }

  priceDropAlert(productName, oldPrice, newPrice) {
    const savings = oldPrice - newPrice;
    this.toast.success(
      "Preço Caiu! 💰",
      `${productName} agora custa R$ ${newPrice.toFixed(2)} (economia de R$ ${savings.toFixed(2)})`,
      {
        duration: 8000,
        actions: [
          {
            label: "Comprar Agora",
            icon: "fa-shopping-cart",
            style: "btn-primary",
            handler: () => this.addToCartAndRedirect(productName),
          },
        ],
      },
    );
  }

  backInStock(productName) {
    this.toast.success(
      "Produto Disponível! 📦",
      `${productName} voltou ao estoque`,
      {
        duration: 6000,
        actions: [
          {
            label: "Comprar",
            icon: "fa-shopping-cart",
            style: "btn-primary",
            handler: () => this.addToCartAndRedirect(productName),
          },
        ],
      },
    );
  }

  listShared(listName) {
    this.toast.success(
      "Lista Compartilhada! 🔗",
      `Sua lista "${listName}" foi compartilhada com sucesso`,
      { duration: 3000 },
    );
  }

  addToCartAndRedirect(productName) {
    // Lógica para adicionar ao carrinho
    console.log(`Adicionando ${productName} ao carrinho...`);
    // Redirecionar para o carrinho
    setTimeout(() => {
      window.location.href = "cart.html";
    }, 500);
  }
}

// ===== SISTEMA DE PROMOÇÕES =====
class PromotionNotifications {
  constructor(toastSystem) {
    this.toast = toastSystem;
  }

  couponApplied(couponCode, discount) {
    this.toast.success(
      "Cupom Aplicado! 🎫",
      `Cupom ${couponCode} aplicado com sucesso! Desconto de ${discount}`,
      { duration: 4000 },
    );
  }

  couponExpired(couponCode) {
    this.toast.error(
      "Cupom Expirado",
      `O cupom ${couponCode} não é mais válido`,
      { duration: 3000 },
    );
  }

  flashSale(productName, discount, timeLeft) {
    this.toast.warning(
      "Oferta Relâmpago! ⚡",
      `${productName} com ${discount}% OFF por apenas ${timeLeft}!`,
      {
        duration: 10000,
        persistent: false,
        actions: [
          {
            label: "Ver Oferta",
            icon: "fa-fire",
            style: "btn-warning",
            handler: () =>
              window.open(
                `products.html?flash=${encodeURIComponent(productName)}`,
                "_blank",
              ),
          },
        ],
      },
    );
  }
}

// ===== SISTEMA DE FEEDBACK DE AÇÕES =====
class ActionFeedback {
  constructor(toastSystem) {
    this.toast = toastSystem;
  }

  formSubmitted(formType) {
    const messages = {
      contact: "Mensagem enviada com sucesso! Entraremos em contato em breve.",
      newsletter:
        "Inscrição realizada! Você receberá nossas novidades por email.",
      review: "Avaliação enviada! Obrigado pelo seu feedback.",
      checkout:
        "Pedido realizado com sucesso! Você receberá um email de confirmação.",
    };

    this.toast.success(
      "Sucesso!",
      messages[formType] || "Ação realizada com sucesso!",
      { duration: 4000 },
    );
  }

  formError(errorMessage) {
    this.toast.error(
      "Erro no Formulário",
      errorMessage || "Ocorreu um erro. Tente novamente.",
      { duration: 4000 },
    );
  }

  copied(content = "Link") {
    this.toast.info(
      "Copiado! 📋",
      `${content} copiado para a área de transferência`,
      { duration: 2000 },
    );
  }

  networkError() {
    this.toast.error(
      "Erro de Conexão",
      "Verifique sua conexão com a internet e tente novamente",
      {
        duration: 6000,
        actions: [
          {
            label: "Tentar Novamente",
            icon: "fa-redo",
            style: "btn-primary",
            handler: () => window.location.reload(),
          },
        ],
      },
    );
  }
}

// ===== INICIALIZAÇÃO GLOBAL =====
document.addEventListener("DOMContentLoaded", () => {
  // Criar instâncias globais
  window.toastSystem = new ToastSystem();
  window.cartNotifications = new CartNotifications(window.toastSystem);
  window.wishlistNotifications = new WishlistNotifications(window.toastSystem);
  window.promotionNotifications = new PromotionNotifications(
    window.toastSystem,
  );
  window.actionFeedback = new ActionFeedback(window.toastSystem);

  // Exemplo de uso automático
  console.log("🍞 Sistema de Toast carregado com sucesso!");

  // Event listeners globais para demonstração
  document.addEventListener("click", (e) => {
    // Detectar cliques em botões de adicionar ao carrinho
    if (e.target.matches('.add-to-cart, [data-action="add-to-cart"]')) {
      const productName =
        e.target.getAttribute("data-product-name") || "Produto";
      window.cartNotifications.itemAdded(productName);
    }

    // Detectar cliques em botões de favoritar
    if (e.target.matches('.add-to-wishlist, [data-action="add-to-wishlist"]')) {
      const productName =
        e.target.getAttribute("data-product-name") || "Produto";
      window.wishlistNotifications.itemAdded(productName);
    }

    // Detectar cliques em botões de copiar
    if (e.target.matches('.copy-button, [data-action="copy"]')) {
      const content = e.target.getAttribute("data-copy-content") || "Conteúdo";
      window.actionFeedback.copied(content);
    }
  });

  // Detectar erros de rede
  window.addEventListener("offline", () => {
    window.toastSystem.warning(
      "Sem Conexão",
      "Você está offline. Algumas funcionalidades podem não funcionar.",
      { duration: 0, persistent: true },
    );
  });

  window.addEventListener("online", () => {
    window.toastSystem.success(
      "Conexão Restaurada",
      "Você está online novamente!",
      { duration: 3000 },
    );
    // Limpar toast de offline
    window.toastSystem.hideAll();
  });

  // Toast de boas-vindas (apenas em desenvolvimento)
  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
  ) {
    setTimeout(() => {
      window.toastSystem.info(
        "Modo Desenvolvimento",
        "Sistema de notificações ativo! 🚀",
        { duration: 3000 },
      );
    }, 1000);
  }
});

// Export para uso em módulos
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    ToastSystem,
    CartNotifications,
    WishlistNotifications,
    PromotionNotifications,
    ActionFeedback,
  };
}
