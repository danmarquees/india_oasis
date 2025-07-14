/**
 * India Oasis - Sistema de Classificação por Estrelas
 *
 * Este script fornece funcionalidades para criar, renderizar e interagir
 * com sistemas de classificação por estrelas em todo o site.
 *
 * Funcionalidades:
 * - Renderização de estrelas estáticas (somente exibição)
 * - Classificação interativa (para avaliações de usuários)
 * - Suporte a classificações fracionárias (meia estrela)
 * - Animações e efeitos visuais
 * - Opções de personalização
 */

class StarRating {
  /**
   * Inicializa um novo sistema de classificação por estrelas
   * @param {Object} options - Opções de configuração
   * @param {string} options.selector - Seletor CSS para o elemento que conterá a classificação
   * @param {number} options.initialValue - Valor inicial (0-5)
   * @param {boolean} options.readOnly - Se a classificação é apenas para exibição
   * @param {number} options.maxStars - Número máximo de estrelas (padrão: 5)
   * @param {Function} options.onChange - Callback chamado quando o valor muda
   * @param {boolean} options.halfStar - Permitir meia estrela
   * @param {boolean} options.showValue - Mostrar valor numérico
   * @param {string} options.starColor - Cor das estrelas (CSS válido)
   * @param {string} options.emptyColor - Cor das estrelas vazias (CSS válido)
   */
  constructor(options) {
    this.options = Object.assign(
      {
        selector: null,
        initialValue: 0,
        readOnly: false,
        maxStars: 5,
        onChange: null,
        halfStar: true,
        showValue: false,
        starColor: "#ffba08",
        emptyColor: "#cccccc",
        size: "medium", // small, medium, large
        tooltips: ["Péssimo", "Ruim", "Regular", "Bom", "Excelente"],
      },
      options,
    );

    this.value = this.options.initialValue;
    this.container = document.querySelector(this.options.selector);

    if (!this.container) {
      console.error(
        `Elemento com seletor ${this.options.selector} não encontrado.`,
      );
      return;
    }

    this.init();
  }

  /**
   * Inicializa o componente de classificação
   */
  init() {
    // Verificar se o contêiner já tem um componente de classificação
    if (this.container.querySelector(".star-rating-component")) {
      return; // Evitar múltiplas inicializações no mesmo contêiner
    }

    // Limpar o contêiner antes de inicializar
    this.container.innerHTML = "";

    // Configurar o contêiner
    this.container.classList.add("star-rating-component");

    if (this.options.size === "small") {
      this.container.classList.add("star-rating-small");
    } else if (this.options.size === "large") {
      this.container.classList.add("star-rating-large");
    }

    // Criar elemento para as estrelas
    this.starsContainer = document.createElement("div");
    this.starsContainer.className = "stars-container";
    this.container.appendChild(this.starsContainer);

    // Criar estrelas
    this.stars = [];
    for (let i = 0; i < this.options.maxStars; i++) {
      const star = document.createElement("span");
      star.className = "rating-star";
      star.innerHTML = '<i class="far fa-star"></i>';
      star.dataset.value = i + 1;

      // Adicionar tooltip se disponível
      if (this.options.tooltips && this.options.tooltips[i]) {
        star.title = this.options.tooltips[i];
      }

      this.starsContainer.appendChild(star);
      this.stars.push(star);

      // Adicionar eventos apenas se não for somente leitura
      if (!this.options.readOnly) {
        star.addEventListener("click", this.handleStarClick.bind(this));
        star.addEventListener("mouseover", this.handleStarHover.bind(this));
        star.addEventListener("mouseout", this.handleStarOut.bind(this));
      }
    }

    // Criar elemento para exibir valor numérico (opcional)
    if (this.options.showValue) {
      this.valueDisplay = document.createElement("span");
      this.valueDisplay.className = "rating-value-display";
      this.container.appendChild(this.valueDisplay);
    }

    // Renderizar o valor inicial
    this.render();
  }

  /**
   * Renderiza as estrelas com base no valor atual
   */
  render() {
    // Atualizar a exibição das estrelas
    this.stars.forEach((star, index) => {
      const starIcon = star.querySelector("i");
      const starValue = index + 1;

      if (starValue <= this.value) {
        // Estrela cheia
        starIcon.className = "fas fa-star";
        starIcon.style.color = this.options.starColor;
      } else if (this.options.halfStar && starValue - 0.5 <= this.value) {
        // Meia estrela
        starIcon.className = "fas fa-star-half-alt";
        starIcon.style.color = this.options.starColor;
      } else {
        // Estrela vazia
        starIcon.className = "far fa-star";
        starIcon.style.color = this.options.emptyColor;
      }
    });

    // Atualizar exibição do valor numérico
    if (this.options.showValue && this.valueDisplay) {
      this.valueDisplay.textContent = this.value.toFixed(1);
    }
  }

  /**
   * Manipula o clique em uma estrela
   * @param {Event} event - O evento de clique
   */
  handleStarClick(event) {
    if (this.options.readOnly) return;

    const star = event.currentTarget;
    let value = parseFloat(star.dataset.value);

    // Suporte para meia estrela
    if (this.options.halfStar) {
      const rect = star.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const halfWidth = rect.width / 2;

      // Se o clique foi na primeira metade da estrela
      if (x < halfWidth) {
        value -= 0.5;
      }
    }

    this.setValue(value);

    // Adicionar efeito de pulso para feedback visual
    star.classList.add("pulse");
    setTimeout(() => {
      star.classList.remove("pulse");
    }, 300);

    // Chamar callback se existir
    if (typeof this.options.onChange === "function") {
      this.options.onChange(this.value);
    }
  }

  /**
   * Manipula o hover sobre uma estrela
   * @param {Event} event - O evento de hover
   */
  handleStarHover(event) {
    if (this.options.readOnly) return;

    const star = event.currentTarget;
    const value = parseFloat(star.dataset.value);

    // Realçar todas as estrelas até a atual
    this.stars.forEach((s, index) => {
      const starValue = index + 1;
      const starIcon = s.querySelector("i");

      if (starValue <= value) {
        starIcon.className = "fas fa-star";
        starIcon.style.color = this.options.starColor;
        s.classList.add("hovered");
      } else {
        starIcon.className = "far fa-star";
        starIcon.style.color = this.options.emptyColor;
        s.classList.remove("hovered");
      }
    });
  }

  /**
   * Manipula a saída do hover de uma estrela
   */
  handleStarOut() {
    if (this.options.readOnly) return;

    // Restaurar a renderização normal
    this.stars.forEach((star) => star.classList.remove("hovered"));
    this.render();
  }

  /**
   * Define o valor da classificação
   * @param {number} value - O novo valor
   */
  setValue(value) {
    // Garantir que o valor está dentro dos limites
    this.value = Math.max(0, Math.min(this.options.maxStars, value));
    this.render();
    return this;
  }

  /**
   * Obtém o valor atual da classificação
   * @returns {number} O valor atual
   */
  getValue() {
    return this.value;
  }

  /**
   * Define a classificação como somente leitura
   * @param {boolean} readOnly - Se a classificação deve ser somente leitura
   */
  setReadOnly(readOnly) {
    this.options.readOnly = readOnly;

    // Remover eventos se for somente leitura
    this.stars.forEach((star) => {
      if (readOnly) {
        star.removeEventListener("click", this.handleStarClick);
        star.removeEventListener("mouseover", this.handleStarHover);
        star.removeEventListener("mouseout", this.handleStarOut);
        star.style.cursor = "default";
      } else {
        star.addEventListener("click", this.handleStarClick.bind(this));
        star.addEventListener("mouseover", this.handleStarHover.bind(this));
        star.addEventListener("mouseout", this.handleStarOut.bind(this));
        star.style.cursor = "pointer";
      }
    });

    return this;
  }

  /**
   * Limpa a classificação (define para 0)
   */
  clear() {
    this.setValue(0);
    return this;
  }

  /**
   * Destrói o componente e remove eventos
   */
  destroy() {
    // Remover eventos
    this.stars.forEach((star) => {
      star.removeEventListener("click", this.handleStarClick);
      star.removeEventListener("mouseover", this.handleStarHover);
      star.removeEventListener("mouseout", this.handleStarOut);
    });

    // Limpar o contêiner
    this.container.innerHTML = "";
    this.container.classList.remove(
      "star-rating-component",
      "star-rating-small",
      "star-rating-large",
    );
  }
}

// Função auxiliar para criar uma classificação somente leitura
function createReadOnlyRating(selector, value, options = {}) {
  // Remover componentes de classificação existentes para o seletor
  const container = document.querySelector(selector);
  if (container) {
    const existingComponent = container.querySelector(".star-rating-component");
    if (existingComponent) {
      existingComponent.remove();
    }
  }

  return new StarRating({
    selector,
    initialValue: value,
    readOnly: true,
    ...options,
  });
}

// Função auxiliar para criar uma classificação interativa
function createInteractiveRating(
  selector,
  initialValue,
  onChange,
  options = {},
) {
  // Remover componentes de classificação existentes para o seletor
  const container = document.querySelector(selector);
  if (container) {
    const existingComponent = container.querySelector(".star-rating-component");
    if (existingComponent) {
      existingComponent.remove();
    }
  }

  return new StarRating({
    selector,
    initialValue,
    onChange,
    ...options,
  });
}

// Inicializar classificações existentes no carregamento da página
document.addEventListener("DOMContentLoaded", () => {
  // Limpar quaisquer componentes de estrelas existentes
  document.querySelectorAll(".star-rating-component").forEach((element) => {
    element.remove();
  });

  // Inicializar apenas a primeira classificação somente leitura
  const displayElement = document.querySelector("[data-rating-display]");
  if (displayElement) {
    const value = parseFloat(displayElement.dataset.ratingValue || 0);
    createReadOnlyRating(`#${displayElement.id}`, value, {
      halfStar: true,
      size: displayElement.dataset.ratingSize || "medium",
      showValue: displayElement.dataset.showValue === "true",
    });
  }

  // Inicializar apenas a primeira classificação interativa
  const inputElement = document.querySelector("[data-rating-input]");
  if (inputElement) {
    const initialValue = parseFloat(inputElement.dataset.ratingValue || 0);
    const hiddenInput = document.querySelector(
      inputElement.dataset.ratingTarget,
    );

    createInteractiveRating(
      `#${inputElement.id}`,
      initialValue,
      (value) => {
        // Atualizar input oculto se existir
        if (hiddenInput) {
          hiddenInput.value = value;
        }

        // Disparar evento personalizado
        const event = new CustomEvent("rating:change", {
          detail: { value, target: inputElement.dataset.ratingTarget },
        });
        inputElement.dispatchEvent(event);
      },
      {
        halfStar: inputElement.dataset.halfStar === "true",
        size: inputElement.dataset.ratingSize || "medium",
        showValue: inputElement.dataset.showValue === "true",
      },
    );
  }
});

// Exportar para uso global
window.StarRating = StarRating;
window.createReadOnlyRating = createReadOnlyRating;
window.createInteractiveRating = createInteractiveRating;
