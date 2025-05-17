"""
Multilanguage support module for the Telegram Cover Bot.
This module provides translation and localization capabilities.
"""
from typing import Dict, Any, Optional, List

# Supported languages
SUPPORTED_LANGUAGES = {
    'ar': 'العربية',  # Arabic
    'en': 'English',   # English
    'es': 'Español',   # Spanish
    'fr': 'Français',  # French
    'ru': 'Русский',   # Russian
}

# Default language
DEFAULT_LANGUAGE = 'ar'

class TranslationManager:
    """Manager for translations and localization."""
    
    def __init__(self):
        """Initialize the translation manager."""
        self._translations = self._load_translations()
        self.user_languages = {}  # Store user language preferences
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """
        Load all translations.
        
        Returns:
            Dictionary of translations by language code
        """
        translations = {}
        
        # Arabic translations
        translations['ar'] = {
            # General messages
            'welcome': 'مرحباً {user}! 👋\n\nأنا بوت جلب أغلفة الأغاني. 🎵🖼️\n\nيمكنك إرسال اسم أغنية، فنان، أو ألبوم وسأقوم بالبحث عن الغلاف بأعلى جودة ممكنة.\n\nاستخدم الأوامر التالية:\n/search - للبحث عن أغنية\n/artist - للبحث عن فنان\n/album - للبحث عن ألبوم\n/help - لعرض المساعدة\n/language - لتغيير اللغة\n\nأو يمكنك ببساطة إرسال اسم الأغنية مباشرة!\n\nتم تطوير البوت بواسطة @T8_WY',
            'help_intro': 'هذا الأمر يعرض جميع أوامر البوت المتاحة مع شرح بسيط لكل أمر:\n\n',
            'help': '🎵 *بوت جلب أغلفة الأغاني* 🖼️\n\n*الأوامر المتاحة:*\n/start - بدء استخدام البوت\n/search - البحث عن أغنية (مثال: /search Bohemian Rhapsody)\n/artist - البحث عن فنان (مثال: /artist Queen)\n/album - البحث عن ألبوم (مثال: /album A Night at the Opera)\n/help - عرض هذه المساعدة\n/language - تغيير اللغة\n/stats - عرض إحصائيات الاستخدام\n/share - مشاركة البوت\n\n*استخدام مباشر:*\nيمكنك أيضاً إرسال اسم الأغنية أو الفنان أو الألبوم مباشرة بدون أوامر.\n\n*ملاحظات:*\n- البوت يقوم بجلب أغلفة الأغاني بأعلى جودة ممكنة\n- يمكنك النقر على زر \'عرض المزيد من النتائج\' للحصول على نتائج إضافية\n- إذا لم تجد ما تبحث عنه، حاول استخدام كلمات مفتاحية مختلفة\n\nتم تطوير البوت بواسطة @T8_WY',
            'language_changed': 'تم تغيير اللغة إلى العربية.',
            'select_language': 'اختر اللغة:',
            'no_results': 'لم يتم العثور على نتائج لـ \'{query}\'.\nالرجاء المحاولة بكلمات مفتاحية مختلفة.',
            'results_found': 'تم العثور على {count} نتيجة لـ \'{query}\'.\nاختر من النتائج التالية:',
            'loading_cover': 'جاري تحميل الغلاف...',
            'error_loading': 'عذراً، حدث خطأ أثناء تحميل الغلاف.',
            'no_cover_found': 'عذراً، لا يمكن العثور على غلاف لهذه الأغنية.',
            'invalid_image': 'عذراً، الصورة غير صالحة: {error}',
            'image_quality': '📊 جودة الصورة: {width}×{height} بكسل',
            'share_message': 'شارك هذا البوت مع أصدقائك:',
            'share_text': '🎵 وجدت بوت رائع لجلب أغلفة الأغاني بجودة عالية! جربه الآن: https://t.me/{bot_username}',
            'stats_title': '📊 *إحصائيات الاستخدام*',
            'stats_searches': 'عدد عمليات البحث: {count}',
            'stats_songs': 'أغاني: {count}',
            'stats_artists': 'فنانين: {count}',
            'stats_albums': 'ألبومات: {count}',
            'stats_most_searched': 'الأكثر بحثاً: {item}',
            'stats_last_search': 'آخر بحث: {query} ({time})',
            'stats_success_rate': 'معدل النجاح: {rate}%',
            
            # Group support
            'group_search_start': '🔍 بحث جماعي: \"{query}\"\n\nتم بدء البحث بواسطة {user}.\nاستخدم الأزرار أدناه للتصويت على نوع البحث:',
            'group_vote_closed': '🔍 بحث جماعي: \"{query}\"\n\nتم إغلاق التصويت. النتيجة: البحث كـ {type} (عدد الأصوات: {count}).\nجاري البحث...',
            'group_results': '🔍 نتائج البحث لـ \"{query}\" (كـ {type}):\n\nتم العثور على {count} نتيجة. اختر من القائمة أدناه:',
            'group_no_active_poll': 'لا يوجد تصويت نشط حالياً. استخدم /groupsearch لبدء بحث جديد.',
            'group_voting_closed': 'التصويت مغلق. البحث قيد التنفيذ أو مكتمل.',
            'group_invalid_vote': 'خيار غير صالح. الخيارات المتاحة: song, artist, album',
            'group_no_results': 'لا توجد نتائج بحث سابقة لهذه المجموعة.',
            'group_last_results': '📊 نتائج آخر بحث:\n\n🔍 استعلام: \"{query}\"\n🔎 نوع البحث: {type}\n📈 عدد النتائج: {count}\n\nاستخدم /groupsearch للبدء في بحث جديد.',
            'group_current_votes': '🔍 بحث جماعي: \"{query}\"\n\nالتصويت الحالي:\n🎵 أغنية: {song_votes} صوت\n👤 فنان: {artist_votes} صوت\n💿 ألبوم: {album_votes} صوت\n\nاستخدم الأزرار أدناه للتصويت، أو أرسل /vote [نوع البحث]',
            'group_initiator_only': 'فقط منشئ البحث يمكنه إنهاء التصويت.',
            'group_selected_result': '🎵 تم اختيار: {title} - {artist}\n\nهنا سيتم إرسال صورة الغلاف بأعلى جودة.',
            
            # Buttons
            'btn_song': '🎵 أغنية',
            'btn_artist': '👤 فنان',
            'btn_album': '💿 ألبوم',
            'btn_finalize': '✅ إنهاء التصويت وبدء البحث',
            'btn_prev': '⬅️ السابق',
            'btn_next': 'التالي ➡️',
            'btn_share_telegram': 'مشاركة عبر تليجرام',
            'btn_share_twitter': 'مشاركة عبر تويتر',
            'btn_share_facebook': 'مشاركة عبر فيسبوك',
            'btn_share_whatsapp': 'مشاركة عبر واتساب',
        }
        
        # English translations
        translations['en'] = {
            # General messages
            'welcome': 'Welcome {user}! 👋\n\nI am a Song Cover Fetching Bot. 🎵🖼️\n\nYou can send me a song name, artist, or album and I will search for the cover with the highest quality possible.\n\nUse the following commands:\n/search - to search for a song\n/artist - to search for an artist\n/album - to search for an album\n/help - to display help\n/language - to change language\n\nOr you can simply send the song name directly!\n\nDeveloped by @T8_WY',
            'help_intro': 'This command displays all available bot commands with a brief explanation for each:\n\n',
            'help': '🎵 *Song Cover Fetching Bot* 🖼️\n\n*Available Commands:*\n/start - Start using the bot\n/search - Search for a song (example: /search Bohemian Rhapsody)\n/artist - Search for an artist (example: /artist Queen)\n/album - Search for an album (example: /album A Night at the Opera)\n/help - Display this help\n/language - Change language\n/stats - View usage statistics\n/share - Share the bot\n\n*Direct Usage:*\nYou can also send the song, artist, or album name directly without commands.\n\n*Notes:*\n- The bot fetches song covers with the highest quality possible\n- You can click on the \'Show more results\' button to get additional results\n- If you don\'t find what you\'re looking for, try using different keywords\n\nDeveloped by @T8_WY',
            'language_changed': 'Language changed to English.',
            'select_language': 'Select language:',
            'no_results': 'No results found for \'{query}\'.\nPlease try with different keywords.',
            'results_found': 'Found {count} results for \'{query}\'.\nChoose from the following results:',
            'loading_cover': 'Loading cover...',
            'error_loading': 'Sorry, an error occurred while loading the cover.',
            'no_cover_found': 'Sorry, no cover could be found for this song.',
            'invalid_image': 'Sorry, the image is invalid: {error}',
            'image_quality': '📊 Image quality: {width}×{height} pixels',
            'share_message': 'Share this bot with your friends:',
            'share_text': '🎵 I found an amazing bot for fetching high-quality song covers! Try it now: https://t.me/{bot_username}',
            'stats_title': '📊 *Usage Statistics*',
            'stats_searches': 'Number of searches: {count}',
            'stats_songs': 'Songs: {count}',
            'stats_artists': 'Artists: {count}',
            'stats_albums': 'Albums: {count}',
            'stats_most_searched': 'Most searched: {item}',
            'stats_last_search': 'Last search: {query} ({time})',
            'stats_success_rate': 'Success rate: {rate}%',
            
            # Group support
            'group_search_start': '🔍 Group search: \"{query}\"\n\nSearch initiated by {user}.\nUse the buttons below to vote on the search type:',
            'group_vote_closed': '🔍 Group search: \"{query}\"\n\nVoting closed. Result: Search as {type} (Vote count: {count}).\nSearching...',
            'group_results': '🔍 Search results for \"{query}\" (as {type}):\n\nFound {count} results. Choose from the list below:',
            'group_no_active_poll': 'No active poll. Use /groupsearch to start a new search.',
            'group_voting_closed': 'Voting is closed. Search is in progress or completed.',
            'group_invalid_vote': 'Invalid option. Available options: song, artist, album',
            'group_no_results': 'No previous search results for this group.',
            'group_last_results': '📊 Last search results:\n\n🔍 Query: \"{query}\"\n🔎 Search type: {type}\n📈 Number of results: {count}\n\nUse /groupsearch to start a new search.',
            'group_current_votes': '🔍 Group search: \"{query}\"\n\nCurrent votes:\n🎵 Song: {song_votes} votes\n👤 Artist: {artist_votes} votes\n💿 Album: {album_votes} votes\n\nUse the buttons below to vote, or send /vote [search type]',
            'group_initiator_only': 'Only the search initiator can end the voting.',
            'group_selected_result': '🎵 Selected: {title} - {artist}\n\nThe cover image will be sent here with the highest quality.',
            
            # Buttons
            'btn_song': '🎵 Song',
            'btn_artist': '👤 Artist',
            'btn_album': '💿 Album',
            'btn_finalize': '✅ End voting and start search',
            'btn_prev': '⬅️ Previous',
            'btn_next': 'Next ➡️',
            'btn_share_telegram': 'Share on Telegram',
            'btn_share_twitter': 'Share on Twitter',
            'btn_share_facebook': 'Share on Facebook',
            'btn_share_whatsapp': 'Share on WhatsApp',
        }
        
        # Spanish translations
        translations['es'] = {
            # General messages
            'welcome': '¡Bienvenido {user}! 👋\n\nSoy un Bot de Búsqueda de Portadas de Canciones. 🎵🖼️\n\nPuedes enviarme un nombre de canción, artista o álbum y buscaré la portada con la mejor calidad posible.\n\nUsa los siguientes comandos:\n/search - para buscar una canción\n/artist - para buscar un artista\n/album - para buscar un álbum\n/help - para mostrar ayuda\n/language - para cambiar el idioma\n\n¡O simplemente puedes enviar el nombre de la canción directamente!\n\nDesarrollado por @T8_WY',
            'help_intro': 'Este comando muestra todos los comandos disponibles del bot con una breve explicación para cada uno:\n\n',
            'help': '🎵 *Bot de Búsqueda de Portadas de Canciones* 🖼️\n\n*Comandos Disponibles:*\n/start - Comenzar a usar el bot\n/search - Buscar una canción (ejemplo: /search Bohemian Rhapsody)\n/artist - Buscar un artista (ejemplo: /artist Queen)\n/album - Buscar un álbum (ejemplo: /album A Night at the Opera)\n/help - Mostrar esta ayuda\n/language - Cambiar idioma\n/stats - Ver estadísticas de uso\n/share - Compartir el bot\n\n*Uso Directo:*\nTambién puedes enviar el nombre de la canción, artista o álbum directamente sin comandos.\n\n*Notas:*\n- El bot obtiene portadas de canciones con la mejor calidad posible\n- Puedes hacer clic en el botón \'Mostrar más resultados\' para obtener resultados adicionales\n- Si no encuentras lo que buscas, intenta usar palabras clave diferentes\n\nDesarrollado por @T8_WY',
            'language_changed': 'Idioma cambiado a Español.',
            'select_language': 'Seleccionar idioma:',
            'no_results': 'No se encontraron resultados para \'{query}\'.\nPor favor, intenta con palabras clave diferentes.',
            'results_found': 'Se encontraron {count} resultados para \'{query}\'.\nElige entre los siguientes resultados:',
            'loading_cover': 'Cargando portada...',
            'error_loading': 'Lo siento, ocurrió un error al cargar la portada.',
            'no_cover_found': 'Lo siento, no se pudo encontrar una portada para esta canción.',
            'invalid_image': 'Lo siento, la imagen no es válida: {error}',
            'image_quality': '📊 Calidad de imagen: {width}×{height} píxeles',
            'share_message': 'Comparte este bot con tus amigos:',
            'share_text': '🎵 ¡Encontré un bot increíble para obtener portadas de canciones de alta calidad! Pruébalo ahora: https://t.me/{bot_username}',
            'stats_title': '📊 *Estadísticas de Uso*',
            'stats_searches': 'Número de búsquedas: {count}',
            'stats_songs': 'Canciones: {count}',
            'stats_artists': 'Artistas: {count}',
            'stats_albums': 'Álbumes: {count}',
            'stats_most_searched': 'Más buscado: {item}',
            'stats_last_search': 'Última búsqueda: {query} ({time})',
            'stats_success_rate': 'Tasa de éxito: {rate}%',
            
            # Group support
            'group_search_start': '🔍 Búsqueda grupal: \"{query}\"\n\nBúsqueda iniciada por {user}.\nUsa los botones a continuación para votar por el tipo de búsqueda:',
            'group_vote_closed': '🔍 Búsqueda grupal: \"{query}\"\n\nVotación cerrada. Resultado: Buscar como {type} (Recuento de votos: {count}).\nBuscando...',
            'group_results': '🔍 Resultados de búsqueda para \"{query}\" (como {type}):\n\nSe encontraron {count} resultados. Elige de la lista a continuación:',
            'group_no_active_poll': 'No hay encuesta activa. Usa /groupsearch para iniciar una nueva búsqueda.',
            'group_voting_closed': 'La votación está cerrada. La búsqueda está en progreso o completada.',
            'group_invalid_vote': 'Opción inválida. Opciones disponibles: song, artist, album',
            'group_no_results': 'No hay resultados de búsqueda anteriores para este grupo.',
            'group_last_results': '📊 Últimos resultados de búsqueda:\n\n🔍 Consulta: \"{query}\"\n🔎 Tipo de búsqueda: {type}\n📈 Número de resultados: {count}\n\nUsa /groupsearch para iniciar una nueva búsqueda.',
            'group_current_votes': '🔍 Búsqueda grupal: \"{query}\"\n\nVotos actuales:\n🎵 Canción: {song_votes} votos\n👤 Artista: {artist_votes} votos\n💿 Álbum: {album_votes} votos\n\nUsa los botones a continuación para votar, o envía /vote [tipo de búsqueda]',
            'group_initiator_only': 'Solo el iniciador de la búsqueda puede finalizar la votación.',
            'group_selected_result': '🎵 Seleccionado: {title} - {artist}\n\nLa imagen de portada se enviará aquí con la mejor calidad.',
            
            # Buttons
            'btn_song': '🎵 Canción',
            'btn_artist': '👤 Artista',
            'btn_album': '💿 Álbum',
            'btn_finalize': '✅ Finalizar votación e iniciar búsqueda',
            'btn_prev': '⬅️ Anterior',
            'btn_next': 'Siguiente ➡️',
            'btn_share_telegram': 'Compartir en Telegram',
            'btn_share_twitter': 'Compartir en Twitter',
            'btn_share_facebook': 'Compartir en Facebook',
            'btn_share_whatsapp': 'Compartir en WhatsApp',
        }
        
        # Add more languages as needed
        
        return translations
    
    def get_text(self, key: str, lang_code: str = None, **kwargs) -> str:
        """
        Get translated text for a key.
        
        Args:
            key: Translation key
            lang_code: Language code (defaults to DEFAULT_LANGUAGE if None)
            **kwargs: Format parameters for the translation
            
        Returns:
            Translated text
        """
        if not lang_code:
            lang_code = DEFAULT_LANGUAGE
            
        # Fallback to default language if the requested language is not supported
        if lang_code not in self._translations:
            lang_code = DEFAULT_LANGUAGE
            
        # Get the translation
        translation = self._translations[lang_code].get(key)
        
        # Fallback to default language if the key is not found
        if translation is None and lang_code != DEFAULT_LANGUAGE:
            translation = self._translations[DEFAULT_LANGUAGE].get(key)
            
        # Fallback to key if translation is still not found
        if translation is None:
            return key
            
        # Format the translation with the provided parameters
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError:
                # If formatting fails, return the raw translation
                return translation
                
        return translation
    
    def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """
        Set a user's preferred language.
        
        Args:
            user_id: Telegram user ID
            lang_code: Language code
            
        Returns:
            True if the language was set successfully, False otherwise
        """
        if lang_code in self._translations:
            self.user_languages[user_id] = lang_code
            return True
        return False
    
    def get_user_language(self, user_id: int) -> str:
        """
        Get a user's preferred language.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Language code
        """
        return self.user_languages.get(user_id, DEFAULT_LANGUAGE)
    
    def get_available_languages(self) -> List[Dict[str, str]]:
        """
        Get a list of available languages.
        
        Returns:
            List of dictionaries with language code and name
        """
        return [
            {'code': code, 'name': name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
