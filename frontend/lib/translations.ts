export const translations = {
    en: {
        title: "SazónBot",
        subtitle: "García Family Recipes",
        signatureRecipes: "Signature Recipes",
        pozole: "Pozole Blanco",
        pozoleDesc: "Traditional hominy soup",
        fajitas: "Fajitas a la Vizcaína",
        fajitasDesc: "Signature dish",
        tuna: "Tortitas de Atún",
        tunaDesc: "Tuna patties",
        footerText: "Authentic recipes from the García family",
        chatTitle: "Recipe Chat",
        chatSubtitle: "Ask me about any Mexican recipe",
        welcome: "Welcome!",
        welcomeText: "Select a recipe from the sidebar or type your own question below.",
        placeholder: "Ask about any recipe...",
        askButton: "Ask",
        searching: "Searching...",
        errorTitle: "Error",
        queryPozole: "How do I make pozole?",
        queryFajitas: "Show me the Fajitas a la Vizcaína recipe",
        queryTuna: "Show me the Tortitas de Atún recipe",
    },
    es: {
        title: "SazónBot",
        subtitle: "Recetas de la Familia García",
        signatureRecipes: "Recetas de la Casa García",
        pozole: "Pozole Blanco",
        pozoleDesc: "Sopa tradicional de maíz pozolero",
        fajitas: "Fajitas a la Vizcaína",
        fajitasDesc: "Platillo especial",
        tuna: "Tortitas de Atún",
        tunaDesc: "Tortitas de atún",
        footerText: "Recetas auténticas de la familia García",
        chatTitle: "Chat de Recetas",
        chatSubtitle: "Pregúntame sobre cualquier receta mexicana",
        welcome: "¡Bienvenidos!",
        welcomeText: "Selecciona una receta del menú o escribe tu propia pregunta abajo.",
        placeholder: "Pregunta sobre cualquier receta...",
        askButton: "Preguntar",
        searching: "Buscando...",
        errorTitle: "Error",
        queryPozole: "¿Cómo hago pozole?",
        queryFajitas: "Muéstrame la receta de Fajitas a la Vizcaína",
        queryTuna: "Muéstrame la receta de Tortitas de Atún",

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