import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control
    property bool primary: false
    property bool danger: false
    readonly property bool filled: primary || danger
    readonly property color tone: danger ? Theme.danger : primary ? Theme.violet : Theme.surface

    implicitHeight: 44
    leftPadding: 18
    rightPadding: 18
    hoverEnabled: true

    font.family: Theme.fontFamily
    font.pixelSize: 14
    font.weight: Font.DemiBold

    contentItem: Text {
        text: control.text
        color: control.filled ? "white" : Theme.text
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        opacity: control.enabled ? 1 : 0.55
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        acceptedButtons: Qt.NoButton
    }

    background: Rectangle {
        radius: 12
        color: !control.enabled ? Qt.lighter(control.tone, 1.25)
             : control.down ? Qt.darker(control.tone, 1.14)
             : control.hovered ? (control.filled ? Qt.lighter(control.tone, 1.08) : Theme.surfaceAlt)
             : control.tone
        border.width: 1
        border.color: control.filled ? "transparent" : (control.hovered ? Theme.borderHover : Theme.border)
        Behavior on color { ColorAnimation { duration: 130 } }
        Behavior on border.color { ColorAnimation { duration: 130 } }

        Rectangle {
            z: -1
            y: control.down ? 1 : 3
            width: parent.width; height: parent.height; radius: parent.radius
            color: control.filled ? Theme.shadowStrong : Theme.shadow
            Behavior on y { NumberAnimation { duration: 90 } }
        }
        Rectangle {
            visible: control.filled
            anchors.fill: parent; radius: parent.radius
            gradient: Gradient {
                GradientStop { position: 0; color: "#26FFFFFF" }
                GradientStop { position: 1; color: "transparent" }
            }
        }
    }
}
