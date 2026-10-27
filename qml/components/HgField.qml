import QtQuick
import QtQuick.Controls
import ".."

TextField {
    id: field
    implicitHeight: 46
    leftPadding: 14; rightPadding: 14
    horizontalAlignment: TextInput.AlignLeft
    verticalAlignment: TextInput.AlignVCenter
    color: Theme.text
    placeholderTextColor: Theme.muted
    selectionColor: Theme.accent
    selectedTextColor: "white"
    font.family: Theme.fontFamily
    font.pixelSize: 14
    hoverEnabled: true
    background: Rectangle {
        radius: 12
        color: field.activeFocus ? Theme.surface : Theme.surfaceAlt
        border.color: field.activeFocus ? Theme.accent : (field.hovered ? Theme.borderHover : Theme.border)
        border.width: field.activeFocus ? 1.5 : 1
        Behavior on border.color { ColorAnimation { duration: 120 } }
        Behavior on color { ColorAnimation { duration: 120 } }
        Rectangle {
            visible: field.activeFocus
            anchors.fill: parent; anchors.margins: -3
            radius: parent.radius + 3
            color: "transparent"
            border.width: 3
            border.color: Theme.accentGlow
        }
        Rectangle {
            z: -1
            visible: !field.activeFocus
            y: 1; width: parent.width; height: parent.height; radius: parent.radius
            color: Theme.shadowSoft
        }
    }
}
