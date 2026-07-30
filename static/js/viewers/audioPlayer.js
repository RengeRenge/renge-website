/**
 * 音频播放器组件
 * Props:
 *   - url: 音频源地址
 *   - file: 当前加载的文件对象 {id, name, thumb, downloadUrl}
 *   - file-list: 音频文件列表（已过滤和排序）
 *   - will-play-id: 准备播放的文件ID
 *   - list: 是否列表模式（从播放列表页面进入）
 *   - show-menu: 是否显示播放列表菜单
 *   - phone-view: 是否手机视图
 *   - app-height: 应用高度（用于菜单大小计算）
 * Events:
 *   - load-file: 用户选择播放文件 {id}
 *   - ended: 当前曲目播放完毕
 *   - playing: 曲目开始播放 {id}
 */
Vue.component('audio-player', {
    template: '\
    <div class="full-ab center" @click="onBackgroundClick" @dblclick="onBackgroundDoubleClick">\
        <div v-if="url && audioCover" class="background" v-bind:style="{backgroundImage: \'url(\' + audioCover + \')\' }"></div>\
        <img v-if="url && audioCover" v-bind:src="audioCover"\
            onerror="this.src=\'/static/image/music_playing.svg\'"\
            style="max-width: 80%; max-height: 80%; position: absolute; border-radius: 4px"\
            v-bind:style="{maxHeight: Math.min(appHeight * 0.8, 400) + \'px\'}">\
        <audio ref="audioEl" v-bind:style="{opacity: audioPlayerOpacity}"\
            v-bind:autoplay="autoPlay ? \'autoplay\' : null" v-bind:loop="autoPlay && loopMode === 2 ? \'loop\' : null"\
            @click="onAudioClick" @ended="onEnded" @play="onPlay" @canplay="onCanplay" preload="auto"\
            controls>\
            <source v-bind:src="url" type="audio/mpeg">\
            <source v-bind:src="url" type="audio/aac">\
            <source v-bind:src="url" type="audio/ogg">\
        </audio>\
        <div v-if="list && fileList.length && showMenu" class="play-list menu-base" @click="onPlaylistDoubleClick"\
            @dblclick="onPlaylistDoubleClick">\
            <div v-if="hasOpenCode" style="padding-left: 14px; padding-top: 5px; padding-bottom: 5px; font-size: 14px;">\
                共享的播放列表</div>\
            <div class="scroll-text">\
                正在播放：{{currentFileName}}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;正在播放：{{currentFileName}}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\
            </div>\
            <input v-if="listSearchState" autofocus="autofocus" class="search-input" v-model="searchText"\
                placeholder="搜索文件名" @input="doSearch">\
            <ul v-bind:style="{maxHeight: Math.min(appHeight - 130, 300) + \'px\'}">\
                <li v-for="(item, index) in displayList" v-bind:class="(index%2 == 0 ? \'odd\' : \'even\') + \' \' +\
                (selectedId == item.id ? \'selected\' : \'\') + \' \' +\
                (willPlayId == item.id ? \'playing\': \'\')" @click="select(item.id)"\
                    @dblclick="onDoubleClick(item.id)" onselectstart="return false">\
                    <img v-if="playingId == item.id" @click="switchPlayState(item.id)"\
                        src="/static/image/list_playing.svg" class="playing-icon">\
                    <div v-else class="playing-icon">{{index + 1}} </div>\
                    <span>\
                        <span class="two_line">{{item.name}}</span>\
                    </span>\
                </li>\
            </ul>\
            <img class="tool" v-bind:class="!autoPlay ? \'tool-disable\' : \'\'" src="/static/image/list_auto.svg"\
                @click="switchAutoPlay">\
            <img class="tool" v-bind:class="!autoPlay ? \'tool-disable\' : \'\'" v-bind:src="loopModes[loopMode]"\
                @click="switchLoopMode">\
            <img class="tool" src="/static/image/list-search.svg" @click="onSearch">\
            <img class="tool" src="/static/image/list_locate.svg" @click="onScrollToPlaying">\
            <img class="tool" src="/static/image/list_next.svg" @click="next(1)">\
        </div>\
    </div>\
    ',
    props: {
        url: { type: String, default: '' },
        file: { type: Object, default: function() { return {} } },
        fileList: { type: Array, default: function() { return [] } },
        willPlayId: { type: [String, Number], default: null },
        list: { type: Boolean, default: false },
        showMenu: { type: Boolean, default: false },
        phoneView: { type: Boolean, default: false },
        appHeight: { type: Number, default: 600 },
        hasOpenCode: { type: Boolean, default: false }
    },
    data: function() {
        return {
            playingId: null,
            selectedId: null,
            displayList: [],
            searchText: '',
            loopMode: 0,
            loopModes: ['/static/image/list_order.svg', '/static/image/list_random.svg', '/static/image/list_one_loop.svg'],
            listSearchState: false,
            audioPlayerOpacity: 1,
            autoPlay: false,
            bgClickTimer: null
        }
    },
    computed: {
        audioCover: function() {
            return this.file && this.file.thumb ? this.file.thumb : ''
        },
        currentFileName: function() {
            return this.file && this.file.name ? this.file.name : ''
        }
    },
    watch: {
        url: function(newUrl) {
            if (newUrl && this.$refs.audioEl) {
                this.$refs.audioEl.load()
            }
        },
        fileList: {
            immediate: true,
            handler: function(list) {
                this.displayList = list
            }
        }
    },
    mounted: function() {
        if (this.url && this.$refs.audioEl) {
            this.$refs.audioEl.load()
        }
    },
    methods: {
        reload: function() {
            if (this.$refs.audioEl) {
                this.$refs.audioEl.load()
            }
        },
        onCanplay: function() {
            if (this.$refs.audioEl) {
                this.$refs.audioEl.play()
            }
        },
        onPlay: function() {
            this.playingId = this.willPlayId
            this.$emit('playing', { id: this.playingId })
            this.registMetaData()
        },
        onEnded: function() {
            if (!this.autoPlay) return
            this.next()
        },
        select: function(fid) {
            this.selectedId = fid
            if (!this.phoneView) return
            this.onItemChoice(fid)
        },
        onDoubleClick: function(fid) {
            if (this.phoneView) return
            this.selectedId = fid
            this.onItemChoice(fid)
        },
        onItemChoice: function(fid) {
            if (this.willPlayId === fid) {
                this.switchPlayState(fid)
            } else {
                if (this.$refs.audioEl) {
                    this.$refs.audioEl.pause()
                }
                this.$emit('load-file', { id: fid })
            }
        },
        switchPlayState: function(fid) {
            if (fid !== this.willPlayId) return
            var el = this.$refs.audioEl
            if (el) {
                if (el.paused) {
                    el.play()
                } else {
                    el.pause()
                }
            }
        },
        next: function(user) {
            var list = this.fileList
            if (!list.length) return

            var currentId = this.playingId || this.willPlayId
            var nextIndex = list.findIndex(function(f) { return f.id === currentId })
            var loopMode = this.loopMode

            if (loopMode === 2 && user) {
                loopMode = 0
            }
            switch (loopMode) {
                case 0:
                    if (nextIndex + 1 < list.length) {
                        nextIndex = nextIndex + 1
                    } else {
                        nextIndex = 0
                    }
                    break
                case 1:
                    nextIndex = Math.floor(Math.random() * list.length)
                    break
                case 2:
                default:
                    return
            }
            this.$emit('load-file', { id: list[nextIndex].id })
        },
        switchLoopMode: function(e) {
            e.cancelBubble = true
            this.loopMode++
            if (this.loopMode >= this.loopModes.length) {
                this.loopMode = 0
            }
        },
        switchAutoPlay: function(e) {
            e.cancelBubble = true
            this.autoPlay = !this.autoPlay
        },
        onSearch: function(e) {
            e.cancelBubble = true
            this.listSearchState = !this.listSearchState
            if (this.listSearchState) {
                this.doSearch()
            } else {
                this.displayList = this.fileList
            }
        },
        doSearch: function() {
            var text = this.searchText.toLowerCase()
            var self = this
            this.displayList = this.fileList.filter(function(file) {
                return file.sortName.indexOf(text) >= 0 || file.name.indexOf(text) >= 0 || file.sortName1.indexOf(text) >= 0
            })
        },
        onScrollToPlaying: function(e) {
            e.cancelBubble = true
            var playingView = document.getElementsByClassName('playing')[0]
            playingView && playingView.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            })
        },
        onPlaylistDoubleClick: function(e) {
            e.cancelBubble = true
        },
        onAudioClick: function(e) {
            e.cancelBubble = true
        },
        onBackgroundClick: function() {
            var self = this
            this.bgClickTimer && clearTimeout(this.bgClickTimer)
            this.bgClickTimer = setTimeout(function() {
                self.audioPlayerOpacity = self.audioPlayerOpacity ? 0 : 1
            }, 200)
        },
        onBackgroundDoubleClick: function() {
            this.bgClickTimer && clearTimeout(this.bgClickTimer)
            if (!document.fullscreenElement) {
                var el = document.documentElement
                if (el.requestFullscreen) el.requestFullscreen()
                else if (el.mozRequestFullScreen) el.mozRequestFullScreen()
                else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen()
                else if (el.msRequestFullscreen) el.msRequestFullscreen()
            } else {
                if (document.exitFullscreen) document.exitFullscreen()
                else if (document.mozCancelFullScreen) document.mozCancelFullScreen()
                else if (document.webkitExitFullscreen) document.webkitExitFullscreen()
                else if (document.msExitFullscreen) document.msExitFullscreen()
            }
        },
        registMetaData: function() {
            var nav = window.navigator
            if (!nav.mediaSession) return

            var file = this.file
            nav.mediaSession.metadata = new MediaMetadata({
                title: file.name,
                artwork: [{ src: file.thumb, type: 'image/png' }]
            })

            var audioEl = this.$refs.audioEl
            if (!audioEl) return

            nav.mediaSession.playbackState = 'playing'

            nav.mediaSession.setActionHandler('play', function() { audioEl.play() })
            nav.mediaSession.setActionHandler('pause', function() { audioEl.pause(); nav.mediaSession.playbackState = 'paused' })
            nav.mediaSession.setActionHandler('stop', function() { audioEl.pause(); audioEl.currentTime = 0; nav.mediaSession.playbackState = 'stopped' })
            nav.mediaSession.setActionHandler('seekbackward', function() { audioEl.currentTime = Math.max(audioEl.currentTime - 10, 0) })
            nav.mediaSession.setActionHandler('seekforward', function() { audioEl.currentTime = Math.min(audioEl.currentTime + 10, audioEl.duration) })
            nav.mediaSession.setActionHandler('seekto', function(details) {
                if (details.seekTime) audioEl.currentTime = Math.min(details.seekTime, audioEl.duration)
            })
            nav.mediaSession.setActionHandler('previoustrack', function() { history.back() })
            var self = this
            nav.mediaSession.setActionHandler('nexttrack', function() { self.next(1) })
        }
    }
})
