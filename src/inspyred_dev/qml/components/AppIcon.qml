import QtQuick

Item {
    id: root

    implicitWidth: 32
    implicitHeight: 32

    Image {
        anchors.fill: parent
        source: '../assets/neon-id-spark-app-icon.png'
        sourceSize.width: Math.max(root.width * 3, 96)
        sourceSize.height: Math.max(root.height * 3, 96)
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
        asynchronous: true
    }
}
