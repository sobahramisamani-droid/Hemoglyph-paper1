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
    background: Rectangle {
        radius: 12
        color: Theme.surface
        border.color: field.activeFocus ? Theme.accent : Theme.border
        border.width: field.activeFocus ? 1.5 : 1
    }
}

