pragma Singleton
import QtQuick

QtObject {
    // Доступные темы: "cyberpunk", "minimal", "retro", "nature", "glass"
    property string currentTheme: "cyberpunk"

    // Цвета для каждой темы
    readonly property var themes: {
        "cyberpunk": {
            "bg1": "#0a0015",
            "bg2": "#1a0033",
            "accent1": "#ff00ff",
            "accent2": "#00ffff",
            "text": "#00ffff",
            "floor": "#050010",
            "wall": "#0a0015"
        },
        "minimal": {
            "bg1": "#ffffff",
            "bg2": "#f5f5f5",
            "accent1": "#333333",
            "accent2": "#666666",
            "text": "#222222",
            "floor": "#e0e0e0",
            "wall": "#ffffff"
        },
        "retro": {
            "bg1": "#c0c0c0",
            "bg2": "#a0a0a0",
            "accent1": "#000080",
            "accent2": "#808080",
            "text": "#000000",
            "floor": "#808080",
            "wall": "#c0c0c0"
        },
        "nature": {
            "bg1": "#e8f5e9",
            "bg2": "#c8e6c9",
            "accent1": "#2e7d32",
            "accent2": "#4caf50",
            "text": "#1b5e20",
            "floor": "#8d6e63",
            "wall": "#e8f5e9"
        },
        "glass": {
            "bg1": "#ffffff",
            "bg2": "#f0f0f0",
            "accent1": "#2196f3",
            "accent2": "#64b5f6",
            "text": "#1565c0",
            "floor": "#e3f2fd",
            "wall": "#ffffff"
        }
    }

    function getTheme() {
        return themes[currentTheme]
    }

    function switchTheme(themeName) {
        if (themes[themeName]) {
            currentTheme = themeName
            console.log("Тема переключена на:", themeName)
        }
    }
}