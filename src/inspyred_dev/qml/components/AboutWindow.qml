import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: root
    objectName: 'aboutWindow'

    required property Window targetWindow

    visible: false
    width: 500
    height: 600
    minimumWidth: 420
    minimumHeight: 500
    title: 'About Inspyred Dev'
    color: Theme.background
    flags: Qt.Window | Qt.FramelessWindowHint
    transientParent: targetWindow

    header: CustomTitleBar {
        targetWindow: root
    }

    function showAbout() {
        show()
        raise()
        requestActivate()
    }

    onVisibleChanged: {
        if (visible) {
            x = targetWindow.x + Math.round((targetWindow.width - width) / 2)
            y = targetWindow.y + Math.round((targetWindow.height - height) / 2)
        }
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.backgroundAlt }
            GradientStop { position: 1; color: Theme.background }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 12

        AppIcon {
            Layout.preferredWidth: 68
            Layout.preferredHeight: 68
            Layout.alignment: Qt.AlignHCenter
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: 'Inspyred Dev'
            color: Theme.textPrimary
            font.pixelSize: 26
            font.weight: Font.Bold
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: 'Version ' + Qt.application.version
            color: Theme.textSecondary
            font.pixelSize: 12
        }

        Text {
            Layout.fillWidth: true
            text: 'Capture what you notice. Turn it into work.'
            color: Theme.textPrimary
            font.pixelSize: 15
            font.weight: Font.DemiBold
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
        }

        GlowLine {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            lineColor: Theme.borderStrong
            strength: 0.5
        }

        Text {
            text: 'Installed plugins'
            color: Theme.textPrimary
            font.pixelSize: 16
            font.weight: Font.DemiBold
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 7

                Repeater {
                    model: Plugins.installedPlugins

                    Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: pluginDetails.implicitHeight + 16
                        radius: 9
                        color: Theme.surface
                        border.color: Theme.border

                        RowLayout {
                            id: pluginDetails
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.name + '  ' + modelData.version
                                    color: Theme.textPrimary
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.origin
                                    color: Theme.textSecondary
                                    font.pixelSize: 11
                                    elide: Text.ElideRight
                                }
                            }

                            Rectangle {
                                implicitWidth: statusText.implicitWidth + 14
                                implicitHeight: 24
                                radius: 8
                                color: modelData.enabled
                                    ? Qt.rgba(Theme.success.r, Theme.success.g, Theme.success.b, 0.14)
                                    : Theme.surfaceAlt
                                border.color: modelData.enabled ? Theme.success : Theme.border

                                Text {
                                    id: statusText
                                    anchors.centerIn: parent
                                    text: modelData.enabled ? 'Enabled' : 'Disabled'
                                    color: modelData.enabled ? Theme.success : Theme.textSecondary
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                }
                            }
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: 'Created by Taylor B. | Inspyre-Softworks · MIT License'
            color: Theme.textSecondary
            font.pixelSize: 11
            horizontalAlignment: Text.AlignHCenter
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 10

            InspyredButton {
                text: 'View on GitHub'
                forceLabel: true
                compact: true
                onClicked: Qt.openUrlExternally('https://github.com/Inspyre-Softworks/inspyred-dev')
            }

            InspyredButton {
                text: 'Close'
                forceLabel: true
                compact: true
                accent: true
                onClicked: root.close()
            }
        }
    }

    WindowResizeHandles {
        anchors.fill: parent
        targetWindow: root
        z: 1000
    }
}
