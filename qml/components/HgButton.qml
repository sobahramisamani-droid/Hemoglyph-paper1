import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control
    property bool primary: false
    property bool danger: false
    
    implicitHeight: 44
    leftPadding: 18
    rightPadding: 18
    
    font.family: Theme.fontFamily
    font.pixelSize: 14
    font.weight: Font.DemiBold

    contentItem: Text {
        text: control.text
        color: control.primary || control.danger ? "white" : Theme.text
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        acceptedButtons: Qt.NoButton
    }

    background: Rectangle {
        radius: 12
        color: control.danger ? (control.down ? "#B42318" : Theme.danger)
             : control.primary ? (control.down ? "#5440C7" : Theme.violet)
             : control.hovered ? Theme.surfaceAlt : Theme.surface
        border.color: control.primary || control.danger ? "transparent" : Theme.border
        
        Behavior on color { 
            ColorAnimation { duration: 130 } 
        }
    }
}