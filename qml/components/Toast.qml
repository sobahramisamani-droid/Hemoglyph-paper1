import QtQuick
import QtQuick.Controls
import ".."

Rectangle {
    id: root
    property string level: "info"
    property alias text: message.text
    width: Math.min(520, message.implicitWidth + 52)
    height: Math.max(52, message.implicitHeight + 24)
    radius: 14
    color: level === "error" ? "#FEF3F2" : level === "warning" ? "#FFFAEB" : level === "success" ? "#ECFDF3" : "#EFF8FF"
    border.color: level === "error" ? "#FDA29B" : level === "warning" ? "#FEC84B" : level === "success" ? "#75E0A7" : "#84CAFF"
    opacity: 0
    visible: opacity > 0
    z: 2000

    Text {
        id: message
        anchors.fill: parent
        anchors.margins: 12
        wrapMode: Text.Wrap
        verticalAlignment: Text.AlignVCenter
        color: level === "error" ? "#B42318" : level === "warning" ? "#B54708" : level === "success" ? "#067647" : "#175CD3"
        font.family: Theme.fontFamily
        font.pixelSize: 13
    }
    Behavior on opacity { NumberAnimation { duration: 180 } }
    Timer { id: timer; interval: 4300; onTriggered: root.opacity = 0 }
    function show(kind, content) { level = kind; text = content; opacity = 1; timer.restart() }
}
