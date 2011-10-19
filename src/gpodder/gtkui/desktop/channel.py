# -*- coding: utf-8 -*-
#
# gPodder - A media aggregator and podcast client
# Copyright (c) 2005-2011 Thomas Perl and the gPodder Team
#
# gPodder is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# gPodder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from gi.repository import Gtk
from gi.repository import Gdk

import gpodder

_ = gpodder.gettext

from gpodder import util
from gpodder.gtkui.interface.common import BuilderWidget


class gPodderChannel(BuilderWidget):
    def new(self):
        self.gPodderChannel.set_title( self.channel.title)
        self.entryTitle.set_text( self.channel.title)
        self.labelURL.set_text(self.channel.url)
        self.cbSkipFeedUpdate.set_active(self.channel.pause_subscription)

        self.combo_section.get_child().set_text(self.channel.section)
        self.section_list = Gtk.ListStore(str)
        for section in sorted(self.sections):
            self.section_list.append([section])
        self.combo_section.set_model(self.section_list)

        self.LabelDownloadTo.set_text( self.channel.save_dir)
        self.LabelWebsite.set_text( self.channel.link)

        if self.channel.auth_username:
            self.FeedUsername.set_text( self.channel.auth_username)
        if self.channel.auth_password:
            self.FeedPassword.set_text( self.channel.auth_password)

        self.cover_downloader.register('cover-available', self.cover_download_finished)
        self.cover_downloader.request_cover(self.channel)

        # Hide the website button if we don't have a valid URL
        if not self.channel.link:
            self.btn_website.hide_all()

        b = Gtk.TextBuffer()
        b.set_text( self.channel.description)
        self.channel_description.set_buffer( b)

        #Add Drag and Drop Support XXX - Currently broken in Gtk3, fixit ;)
        #flags = Gtk.DestDefaults.ALL
        #targets = [ ('text/uri-list', 0, 2), ('text/plain', 0, 4) ]
        #actions = Gdk.DragAction.DEFAULT | Gdk.DragAction.COPY
        #Gtk.drag_dest_set(self.vboxCoverEditor, flags, targets, actions)
        #self.vboxCoverEditor.connect( 'drag_data_received', self.drag_data_received)

    def on_btn_website_clicked(self, widget):
        util.open_website(self.channel.link)

    def on_btnDownloadCover_clicked(self, widget):
        dlg = Gtk.FileChooserDialog(title=_('Select new podcast cover artwork'), parent=self.gPodderChannel, action=Gtk.FileChooserAction.OPEN)
        dlg.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dlg.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        if dlg.run() == Gtk.ResponseType.OK:
            url = dlg.get_uri()
            self.cover_downloader.replace_cover(self.channel, url)

        dlg.destroy()

    def on_btnClearCover_clicked(self, widget):
        self.cover_downloader.replace_cover(self.channel)

    def cover_download_finished(self, channel_url, pixbuf):
        if pixbuf is not None:
            self.imgCover.set_from_pixbuf(pixbuf)
        self.gPodderChannel.show()

    def drag_data_received( self, widget, content, x, y, sel, ttype, time):
        files = sel.data.strip().split('\n')
        if len(files) != 1:
            self.show_message( _('You can only drop a single image or URL here.'), _('Drag and drop'))
            return

        file = files[0]

        if file.startswith('file://') or file.startswith('http://'):
            self.cover_downloader.replace_cover(self.channel, file)
            return

        self.show_message( _('You can only drop local files and http:// URLs here.'), _('Drag and drop'))

    def on_gPodderChannel_destroy(self, widget, *args):
        self.cover_downloader.unregister('cover-available', self.cover_download_finished)

    def on_btnOK_clicked(self, widget, *args):
        self.channel.pause_subscription = self.cbSkipFeedUpdate.get_active()
        self.channel.rename(self.entryTitle.get_text())
        self.channel.auth_username = self.FeedUsername.get_text().strip()
        self.channel.auth_password = self.FeedPassword.get_text()

        new_section = self.combo_section.get_child().get_text().strip()
        if self.channel.section != new_section:
            self.channel.section = new_section
            section_changed = True
        else:
            section_changed = False

        self.channel.save()

        self.cover_downloader.reload_cover_from_disk(self.channel)

        self.gPodderChannel.destroy()

        self.update_podcast_list_model(selected=True,
                sections_changed=section_changed)

