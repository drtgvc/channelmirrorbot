from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
import telegram

import sched, time

from configparser import ConfigParser

config = ConfigParser()
config.read('channelmirror.ini')
token=config.get('bot','token')
fchid=config.get('channel','fchid')
tchid=config.get('channel','tchid')

updater = Updater(token, use_context=True)

"""
this class will wait for some time end then:
    - if group is not empty, push all items in group to channel as media group
    - do nothing if list is empty
    - if media group id is new, flush old media group and start collect new media group
    - if media group is 10 items, flush it to channel in any case
"""
class MediaGroup:

    def __init__(self):
        self.caption = ''
        self.caption_entities=None
        self.media_group_id=None
        self.queue=()
        self.waitNextPush=True
        self.bot=None

        # start ticker
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(5, 1, self.ticker, (self.scheduler,))


    def pushItem(self, bot, media_group_id, item):
        if not item:
            return 
        if not media_group_id:
            return 

        self.bot=bot

        # if group is empty yet 
        if self.media_group_id==None:
            self.media_group_id=media_group_id
            self.queue=[]
            self.queue.append(item)
            # save caption for the first item in the list only 
            print('item')
            print(item)
            #if item.caption: 
            #    self.caption=item.caption
            self.caption='test'
            self.caption_entities=item.caption_entities
        else:
            # if group id is different, flush old items
            if self.media_group_id!=media_group_id:
                self.flushItems()
                return
            self.bot=bot
            self.queue.append(item)

    def flushItems(self):
        if not self.bot:
            if len(self.queue):
                self.queue=()
            return

        self.bot.send_media_group(chat_id=tchid, media=self.queue)

        self.caption = ''
        self.caption_entities=None
        self.media_group_id=None
        self.queue=()
        self.waitNextPush=True
        self.bot=None


    def ticker(self,sc):

        # flush what we have in queue
        if self.waitNextPush:
            self.waitNextPush=False
            self.scheduler.enter(5, 1, self.ticker, (self.scheduler,))
            return

        self.flushItems()

        self.scheduler.enter(5, 1, self.ticker, (self.scheduler,))

    def run(self):
        self.scheduler.run()


mediaGroup = MediaGroup()



def start(update: Update, context: CallbackContext):
	update.message.reply_text("Mirror Bot.Please write\ /help to see the commands available.")

def help(update: Update, context: CallbackContext):
	update.message.reply_text("""Available Commands :-
	/help - To get help
	""")

"""
decotor validates that sender channel is or fchid from ini file
"""
def handler_decorator(func):
    def inner(*args, **kwargs):
        # if it's not our registered sender channel, do nothing 
        if args[0].channel_post.chat.id!=int(fchid):
            return
        return func(*args, **kwargs)
    return inner

@handler_decorator
def mirror_text(update: Update, context: CallbackContext):
    print('text')
    context.bot.send_message(chat_id=tchid, text=update.channel_post.text, entities=update.channel_post.entities)


@handler_decorator
def all(update: Update, context: CallbackContext):
    print('all')
    context.bot.send_message(chat_id=tchid,text=update.channel_post.text)

    #ntext.bot.forward_message(chat_id='@testchannel2_1',from_chat_id=update.channel_post.chat.id,message_id=update.channel_post.message_id)
    
@handler_decorator
def mirror_animation(update: Update, context: CallbackContext):
    print('animation')

@handler_decorator
def mirror_audio(update: Update, context: CallbackContext):
    print('audio')

@handler_decorator
def mirror_contact(update: Update, context: CallbackContext):
    print('contact')

@handler_decorator
def mirror_document(update: Update, context: CallbackContext):
    print('document')
    print(update)
    if not update.channel_post.media_group_id:
        context.bot.send_document(  chat_id=tchid, 
                                    caption=update.channel_post.caption,
                                    document=update.channel_post.document,
                                    caption_entities=update.channel_post.caption_entities)
    else:
        mediaGroup.pushItem(    context.bot, 
                                update.channel_post.media_group_id, 
                                telegram.InputMediaDocument(media=update.channel_post.document, caption=update.channel_post.caption, caption_entities=update.channel_post.caption_entities) )


@handler_decorator
def mirror_photo(update: Update, context: CallbackContext):
    print('photo')
    print(update)
    if not update.channel_post.media_group_id:
        context.bot.send_photo( chat_id=tchid,
                                caption=update.channel_post.caption,
                                photo=update.channel_post.photo[0],
                                caption_entities=update.channel_post.caption_entities)
    else:
        mediaGroup.pushItem(    context.bot, 
                                update.channel_post.media_group_id, 
                                telegram.InputMediaPhoto(media=update.channel_post.photo[0], caption=update.channel_post.caption, caption_entities=update.channel_post.caption_entities) )


@handler_decorator
def mirror_poll(update: Update, context: CallbackContext):
    print('poll')

@handler_decorator
def mirror_sticker(update: Update, context: CallbackContext):
    print('sticker')

@handler_decorator
def mirror_video(update: Update, context: CallbackContext):
    print('video')

@handler_decorator
def mirror_video_note(update: Update, context: CallbackContext):
    print('video_note')



#updater.dispatcher.add_handler(CommandHandler('start', start))
#updater.dispatcher.add_handler(CommandHandler('help', help))
#updater.dispatcher.add_handler(MessageHandler(Filters., mirror_group))
updater.dispatcher.add_handler(MessageHandler(Filters.text, mirror_text))
updater.dispatcher.add_handler(MessageHandler(Filters.animation, mirror_animation))
#updater.dispatcher.add_handler(MessageHandler(Filters.attachment, mirror_attachment))
updater.dispatcher.add_handler(MessageHandler(Filters.audio, mirror_audio))
updater.dispatcher.add_handler(MessageHandler(Filters.contact, mirror_contact))
updater.dispatcher.add_handler(MessageHandler(Filters.document, mirror_document))
updater.dispatcher.add_handler(MessageHandler(Filters.photo, mirror_photo))
updater.dispatcher.add_handler(MessageHandler(Filters.poll, mirror_poll))
updater.dispatcher.add_handler(MessageHandler(Filters.sticker, mirror_sticker))
updater.dispatcher.add_handler(MessageHandler(Filters.video, mirror_video))
updater.dispatcher.add_handler(MessageHandler(Filters.video_note, mirror_video_note))


# Filters out unknown messages.
updater.dispatcher.add_handler(MessageHandler(Filters.all, all))

updater.start_polling()
mediaGroup.run()
