import QtQuick
import QtQuick.Controls
import ".."

// Base surface card used across every page. Dependency-free (no GraphicalEffects), theme-aware.
// Depth comes from two offset shadow layers drawn beneath the card and a faint top sheen.
Rectangle {
    id: card
    color: Theme.surface
    border.width: 1
    border.color: hovered ? Theme.borderHover : Theme.border
    radius: Theme.radius

    property bool interactive: false
    property real hoverScale: 1.005
    property int elevation: 1
    property color edgeColor: "transparent"     // set to show a 4 px accent bar on the left edge
    readonly property bool hovered: interactive && hoverArea.containsMouse

    Behavior on border.color { ColorAnimation { duration: 140 } }

    Rectangle {
        z: -2
        anchors.fill: parent
        anchors.topMargin: 4 * card.elevation + (card.hovered ? 2 : 0)
        anchors.leftMargin: -1; anchors.rightMargin: -1
        radius: card.radius + 1
        color: Theme.shadowSoft
        Behavior on anchors.topMargin { NumberAnimation { duration: 140 } }
    }
    Rectangle {
        z: -1
        anchors.fill: parent
        anchors.topMargin: 2 * card.elevation
        radius: card.radius
        color: Theme.shadow
    }
    Rectangle {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: Math.min(parent.height, 56)
        radius: card.radius
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.sheen }
            GradientStop { position: 1; color: "transparent" }
        }
    }
    Rectangle {
        visible: card.edgeColor.a > 0
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom; margins: 1 }
        anchors.topMargin: 10; anchors.bottomMargin: 10
        width: 4; radius: 2
        color: card.edgeColor
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        cursorShape: card.interactive ? Qt.PointingHandCursor : Qt.ArrowCursor
        hoverEnabled: card.interactive
        acceptedButtons: Qt.NoButton
    }
}
