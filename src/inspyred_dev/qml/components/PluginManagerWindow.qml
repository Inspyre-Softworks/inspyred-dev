import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: root
    objectName: 'pluginManagerWindow'

    required property Window targetWindow
    property string pendingUninstallId: ''

    visible: false
    width: 560
    height: 620
    minimumWidth: 460
    minimumHeight: 520
    title: 'Plugin Manager'
    color: Theme.background
    flags: Qt.Window | Qt.FramelessWindowHint
    transientParent: targetWindow

    header: CustomTitleBar {
        targetWindow: root
    }

    function showManager() {
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
        anchors.margins: 24
        spacing: 12

        Text {
            text: 'Plugin Manager'
            color: Theme.textPrimary
            font.pixelSize: 26
            font.weight: Font.Bold
        }

        Text {
            Layout.fillWidth: true
            text: 'Install integrations and control which plugins load when Inspyred Dev starts.'
            color: Theme.textSecondary
            font.pixelSize: 13
            wrapMode: Text.Wrap
        }

        RowLayout {
            Layout.fillWidth: true

            BusyIndicator {
                visible: Plugins.operationBusy
                running: visible
                implicitWidth: 24
                implicitHeight: 24
            }

            Item { Layout.fillWidth: true }

            InspyredButton {
                text: 'Install ZIP…'
                forceLabel: true
                compact: true
                enabled: !Plugins.operationBusy
                tooltip: 'Install a downloaded plugin ZIP'
                onClicked: pluginFileDialog.open()
            }

            InspyredButton {
                text: 'Install from GitHub…'
                forceLabel: true
                compact: true
                accent: true
                enabled: !Plugins.operationBusy
                tooltip: 'Install from a GitHub repository, branch, or ZIP URL'
                onClicked: githubInstallDialog.open()
            }
        }

        Text {
            Layout.fillWidth: true
            text: 'Plugins run code on this computer. Install only plugins you trust.'
            color: Theme.textSecondary
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 8

                Repeater {
                    model: Plugins.installedPlugins

                    Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        implicitHeight: pluginRow.implicitHeight + 20
                        radius: 10
                        color: Theme.surface
                        border.color: modelData.error.length > 0 ? Theme.danger : Theme.border

                        RowLayout {
                            id: pluginRow
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.name + '  ' + modelData.version
                                    color: Theme.textPrimary
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.pendingRemoval
                                        ? modelData.origin + ' · removal pending'
                                        : modelData.origin + (modelData.active ? ' · active' : '')
                                    color: modelData.pendingRemoval
                                        ? Theme.danger
                                        : Theme.textSecondary
                                    font.pixelSize: 11
                                    elide: Text.ElideRight
                                }

                                Text {
                                    Layout.fillWidth: true
                                    visible: modelData.error.length > 0
                                    text: modelData.error
                                    color: Theme.danger
                                    font.pixelSize: 11
                                    wrapMode: Text.Wrap
                                }
                            }

                            Switch {
                                checked: modelData.enabled
                                enabled: modelData.canDisable && !modelData.pendingRemoval
                                Accessible.name: (checked ? 'Disable ' : 'Enable ') + modelData.name
                                onToggled: {
                                    if (checked !== modelData.enabled)
                                        Plugins.setPluginEnabled(modelData.id, checked)
                                }
                            }

                            InspyredButton {
                                visible: modelData.canUninstall
                                iconName: 'trash'
                                iconOnly: true
                                text: 'Uninstall'
                                compact: true
                                enabled: !modelData.pendingRemoval
                                tooltip: 'Uninstall ' + modelData.name
                                onClicked: {
                                    root.pendingUninstallId = modelData.id
                                    uninstallDialog.open()
                                }
                            }
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: Plugins.operationMessage.length > 0
            text: Plugins.operationMessage
            color: Theme.success
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }

        Text {
            Layout.fillWidth: true
            visible: Plugins.operationError.length > 0
            text: Plugins.operationError
            color: Theme.danger
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }

        InspyredButton {
            Layout.alignment: Qt.AlignRight
            text: 'Close'
            forceLabel: true
            compact: true
            accent: true
            onClicked: root.close()
        }
    }

    FileDialog {
        id: pluginFileDialog
        title: 'Install Inspyred Dev plugin'
        nameFilters: ['Plugin ZIP archives (*.zip)']
        onAccepted: Plugins.installPlugin(selectedFile.toString())
    }

    Dialog {
        id: githubInstallDialog
        title: 'Install plugin from GitHub'
        anchors.centerIn: parent
        width: Math.min(460, root.width - 48)
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel

        onOpened: githubSource.forceActiveFocus()
        onAccepted: Plugins.installPlugin(githubSource.text)

        ColumnLayout {
            width: parent.width
            spacing: 10

            Text {
                Layout.fillWidth: true
                text: 'Enter an HTTPS GitHub repository, branch, release ZIP, or archive URL.'
                color: Theme.textSecondary
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }

            InspyredTextField {
                id: githubSource
                Layout.fillWidth: true
                placeholderText: 'https://github.com/owner/inspyred-plugin'
                helpText: 'Only GitHub-hosted remote archives are accepted'
            }
        }
    }

    Dialog {
        id: uninstallDialog
        title: 'Uninstall plugin?'
        anchors.centerIn: parent
        modal: true
        standardButtons: Dialog.Yes | Dialog.Cancel
        onAccepted: Plugins.uninstallPlugin(root.pendingUninstallId)

        Text {
            width: 360
            text: 'Active plugins are removed after Inspyred Dev restarts.'
            color: Theme.textSecondary
            wrapMode: Text.Wrap
        }
    }

    WindowResizeHandles {
        anchors.fill: parent
        targetWindow: root
        z: 1000
    }
}
