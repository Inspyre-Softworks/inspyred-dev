import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root

    required property string extensionPoint
    property var host: null
    spacing: 12

    Repeater {
        model: Plugins.uiExtensions(root.extensionPoint)

        Loader {
            required property var modelData
            Layout.fillWidth: true
            source: modelData.source

            onLoaded: {
                if (item && item.hasOwnProperty('host'))
                    item.host = root.host
            }
        }
    }
}
