pragma Singleton
import QtQuick

QtObject {
    property bool dark: true
    readonly property color background: dark ? "#0B1020" : "#F4F7FB"
    readonly property color surface: dark ? "#111827" : "#FFFFFF"
    readonly property color surfaceAlt: dark ? "#172033" : "#F8FAFC"
    readonly property color sidebar: "#0A1020"
    readonly property color text: dark ? "#F3F4F6" : "#101828"
    readonly property color muted: dark ? "#94A3B8" : "#667085"
    readonly property color border: dark ? "#263248" : "#E4EAF2"
    readonly property color accent: "#23BFE5"
    readonly property color primary: "#23BFE5"
    readonly property color violet: "#7558F5"
    readonly property color success: "#12B76A"
    readonly property color warning: "#F79009"
    readonly property color danger: "#F04438"
    readonly property color info: "#2E90FA"
    readonly property int radiusSm: 10
    readonly property int radius: 16
    readonly property int radiusLg: 24
    readonly property string fontFamily: "Inter"
}
