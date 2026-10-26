import QtQuick
import QtQuick.Controls
import ".."

// Base surface card used across every page. Keep it dependency-free and theme-aware.
Rectangle {
    id: card
    color: Theme.surface
    border.width: 1
    border.color: Theme.border
    radius: Theme.radius

    // Subtle hover lift for interactive cards.
    property bool interactive: false
    property real hoverScale: 1.005
    readonly property bool hovered: interactive && hoverArea.containsMouse

    Behavior on border.color { ColorAnimation { duration: 140 } }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        cursorShape: card.interactive ? Qt.PointingHandCursor : Qt.ArrowCursor
        hoverEnabled: card.interactive
        acceptedButtons: Qt.NoButton
    }
}
