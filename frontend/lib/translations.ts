export const translations = {
    en: {
      title: "Cocina Familiar",
      subtitle: "Benítez Family Recipes",
      quickRecipes: "Quick Recipes",
      pozole: "Pozole Blanco",
      pozoleDesc: "Traditional hominy soup",
      chicken: "Chicken Dishes",
      chickenDesc: "Chicken recipes",
      soups: "Mexican Soups",
      soupsDesc: "Traditional soups",
      fajitas: "Fajitas a la Vizcaína",
      fajitasDesc: "Signature dish",
      pasta: "Pasta Dishes",
      pastaDesc: "Pasta recipes",
      seafood: "Seafood",
      seafoodDesc: "Seafood dishes",
      footerText: "Authentic recipes from the Benítez family",
      chatTitle: "Recipe Chat",
      chatSubtitle: "Ask me about any Mexican recipe",
      welcome: "Welcome!",
      welcomeText: "Select a recipe from the sidebar or type your own question below.",
      placeholder: "Ask about any recipe...",
      askButton: "Ask",
      searching: "Searching...",
      errorTitle: "Error",
      queryPozole: "How do I make pozole?",
      queryChicken: "Show me chicken recipes",
      querySoups: "What soups do you have?",
      queryFajitas: "Fajitas a la Vizcaina recipe",
      queryPasta: "Show me pasta recipes",
      querySeafood: "Show me seafood recipes",
    },
    es: {
      title: "Cocina Familiar",
      subtitle: "Recetas de la Familia Benítez",
      quickRecipes: "Recetas Rápidas",
      pozole: "Pozole Blanco",
      pozoleDesc: "Sopa tradicional de maíz pozolero",
      chicken: "Platillos de Pollo",
      chickenDesc: "Recetas con pollo",
      soups: "Sopas Mexicanas",
      soupsDesc: "Sopas tradicionales",
      fajitas: "Fajitas a la Vizcaína",
      fajitasDesc: "Platillo especial",
      pasta: "Pastas",
      pastaDesc: "Recetas de pasta",
      seafood: "Mariscos",
      seafoodDesc: "Platillos de mar",
      footerText: "Recetas auténticas de la familia Benítez",
      chatTitle: "Chat de Recetas",
      chatSubtitle: "Pregúntame sobre cualquier receta mexicana",
      welcome: "¡Bienvenidos!",
      welcomeText: "Selecciona una receta del menú o escribe tu propia pregunta abajo.",
      placeholder: "Pregunta sobre cualquier receta...",
      askButton: "Preguntar",
      searching: "Buscando...",
      errorTitle: "Error",
      queryPozole: "¿Cómo hago pozole?",
      queryChicken: "Muéstrame recetas de pollo",
      querySoups: "¿Qué sopas tienes?",
      queryFajitas: "Receta de fajitas a la Vizcaína",
      queryPasta: "Muéstrame recetas de pasta",
      querySeafood: "Muéstrame recetas de mariscos",
    }
  };
  
  export type Language = 'en' | 'es';
  
  export function detectLanguage(): Language {
    if (typeof window === 'undefined') return 'en';
    
    const browserLang = navigator.language.toLowerCase();
    
    if (browserLang.startsWith('es')) {
      return 'es';
    }
    
    return 'en';
  }