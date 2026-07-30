/**
 * EPUB 查看器组件
 * Props:
 *   - file: { thumb, downloadUrl, id, name }
 *   - phone-view: 是否手机视图
 *   - show-menu: 是否显示章节目录菜单
 * Events:
 *   - loaded: { loaded: Boolean, toc: Array|null }
 * Methods (call via $refs):
 *   - open(): 开始加载 EPUB（封面动画 → 阅读器）
 */
Vue.component('epub-viewer', {
    template: '\
    <div>\
        <div v-if="loading" class="epub-viewer full-ab center-column transition">\
            <div class="full-ab center-column transition">\
                <div ref="epubWrapper"\
                    v-bind:class="coverShadow ? epubSizeClass : [\'shadow\', \'epub-bg\', epubSizeClass].join(\' \')"\
                    style="position: absolute;">\
                    <div class="full-ab transition1" style="position: absolute;"\
                        v-bind:style="{opacity: areaOpacity}">\
                        <div key="epubContent" class="full-ab" v-bind:class="phoneView ? \'\' : \'spreads\'" ref="epubArea">\
                        </div>\
                    </div>\
                </div>\
                <a v-if="!phoneView" v-bind:style="{opacity: areaOpacity}" class="epub-arrow epub-arrow-prev"\
                    @click="prev">‹</a>\
                <a v-if="!phoneView" v-bind:style="{opacity: areaOpacity}" class="epub-arrow epub-arrow-next"\
                    @click="next">›</a>\
            </div>\
            <div v-if="!loaded" v-bind:class="coverShadow ? \'shadow transition\': \'\'"\
                v-bind:style="coverShadowStyle">\
                <div v-if="coverShow" class="full-ab epub-bg"></div>\
            </div>\
            <div v-if="!loaded" v-bind:class="epubSizeClass" style="position: absolute;">\
                <img v-if="coverShow" key="epubCover" v-bind:src="thumb"\
                    @error="onThumbError" class="transition" v-bind:style="coverStyle" />\
            </div>\
        </div>\
        <div v-if="showMenu && loaded && toc" class="menu-base epub-chapter-wrapper">\
            <tree-item class="epub-item list-style-none" style="padding:16px;"\
                :item="{label: fileName, subitems: toc}" @select="gotoToc">\
            </tree-item>\
        </div>\
    </div>\
    ',
    props: {
        file: { type: Object, default: function() { return {} } },
        phoneView: { type: Boolean, default: false },
        showMenu: { type: Boolean, default: false }
    },
    data: function() {
        return {
            loading: false,
            loaded: false,
            coverShow: false,
            coverStyle: {},
            coverShadowStyle: {},
            coverShadow: true,
            areaOpacity: 0,
            epubBook: null,
            epubRendition: null,
            toc: null
        }
    },
    computed: {
        epubSizeClass: function() {
            return this.phoneView ? 'epub-size-phone' : 'epub-size'
        },
        thumb: function() {
            return this.file && this.file.thumb ? this.file.thumb : ''
        },
        fileName: function() {
            return this.file && this.file.name ? this.file.name : ''
        },
        downloadUrl: function() {
            return this.file && this.file.downloadUrl ? this.file.downloadUrl : ''
        },
        fileId: function() {
            return this.file && this.file.id ? this.file.id : null
        }
    },
    watch: {
        loaded: function(val) {
            this.$emit('loaded', { loaded: val, toc: this.toc })
        }
    },
    mounted: function() {
        window.addEventListener('resize', this.onResize)
    },
    beforeDestroy: function() {
        window.removeEventListener('resize', this.onResize)
        this.epubRendition = null
        this.epubBook = null
    },
    methods: {
        open: function() {
            if (this.loading || this.loaded) {
                return
            }
            this.$emit('opening')
            var self = this

            var coverEl = document.getElementById('cover')
            if (!coverEl) {
                // no external cover element, directly load
                this.startLoad()
                return
            }

            var style = getFrame(coverEl, true)
            var rate = parseFloat(style.width) / parseFloat(style.height)

            self.loading = true
            self.areaOpacity = 0
            self.coverShadow = true
            self.loaded = false

            self.coverShadowStyle = self.getCoverStyle(rate, coverEl, false)

            self.$nextTick(function() {
                setTimeout(function() {
                    self.coverShadowStyle = self.getCoverStyle(rate, coverEl, false)

                    var wrapperEl = self.$refs.epubWrapper
                    var frame = getFrame(wrapperEl)
                    var cs = self.getCoverStyle(rate, coverEl, false)

                    cs.left = parseFloat(cs.left) - frame.x + 'px'
                    cs.top = parseFloat(cs.top) - frame.y + 'px'
                    self.coverStyle = cs
                    self.coverShow = true

                    self.$nextTick(function() {
                        setTimeout(function() {
                            self.coverStyle = self.getCoverStyle(rate, wrapperEl, true)
                            self.coverShadowStyle = self.getCoverStyle(rate, wrapperEl, false)

                            self.loadEpub(self.$refs.epubArea, self.downloadUrl + '/', function() {
                                self.coverStyle = self.getCoverStyle(rate, wrapperEl, true)
                                self.coverShadowStyle = self.getCoverStyle(rate, wrapperEl, false)

                                self.$nextTick(function() {
                                    setTimeout(function() {
                                        var cs2 = self.getCoverStyle(rate, wrapperEl, true)
                                        cs2.left = (-parseFloat(cs2.width)) + 'px'
                                        self.coverStyle = cs2

                                        var fs = getFrame(wrapperEl, true)
                                        self.coverShadowStyle = fs

                                        self.areaOpacity = 1

                                        self.$nextTick(function() {
                                            setTimeout(function() {
                                                self.coverShadow = false
                                                self.loaded = true
                                            }, 400)
                                        })
                                    }, 400)
                                })
                            })
                        }, 10)
                    })
                }, 10)
            })
        },
        startLoad: function() {
            this.loading = true
            this.areaOpacity = 1
            this.coverShadow = false
            this.loaded = false
            var self = this
            this.$nextTick(function() {
                self.loadEpub(self.$refs.epubArea, self.downloadUrl + '/', function() {
                    self.loaded = true
                })
            })
        },
        getCoverStyle: function(rate, container, relateContainer) {
            var style
            if (typeof container === 'string') {
                style = getFrame(container, true)
            } else {
                style = getFrame(container, true)
            }

            var width = parseFloat(style.width)
            var height = parseFloat(style.height)
            var left = parseFloat(style.left)
            var top = parseFloat(style.top)
            var _rate = width / height

            if (_rate > rate) {
                style.width = height * rate + 'px'
                style.left = (width - height * rate) / 2.0
                if (!relateContainer) {
                    style.left += left
                } else {
                    style.top = 0
                }
                style.left += 'px'
            } else {
                style.height = width / rate + 'px'
                style.top = (height - width / rate) / 2.0
                if (!relateContainer) {
                    style.top += top
                } else {
                    style.left = 0
                }
                style.top += 'px'
            }
            return style
        },
        loadEpub: function(div, url, complete) {
            var book = ePub(url)
            var phoneView = this.phoneView
            var params = {
                flow: phoneView ? 'scrolled' : 'paginated',
                width: '100%',
                height: '100%'
            }
            if (phoneView) {
                params.manager = 'continuous'
            }
            var rendition = book.renderTo(div, params)

            var pageKey = 'epubPage_' + this.fileId
            var cfi = localStorage.getItem(pageKey)
            if (cfi) {
                rendition.display(cfi)
            } else {
                rendition.display()
            }

            this.epubBook = book
            this.epubRendition = rendition

            var self = this
            book.ready.then(function() {
                book.loaded.navigation.then(function(nav) {
                    self.toc = nav.toc
                })

                rendition.on('relocated', function(relocated) {
                    localStorage.setItem(pageKey, relocated.start.cfi)
                })

                setTimeout(function() {
                    complete()
                }, 400)

                if (phoneView) {
                    return
                }

                var keyListener = function(e) {
                    if ((e.keyCode || e.which) == 37) {
                        book.package.metadata.direction === 'rtl' ? rendition.next() : rendition.prev()
                    }
                    if ((e.keyCode || e.which) == 39) {
                        book.package.metadata.direction === 'rtl' ? rendition.prev() : rendition.next()
                    }
                }
                rendition.on('keyup', keyListener)
                document.addEventListener('keyup', keyListener, false)
            })
        },
        prev: function(e) {
            if (!this.epubRendition) return
            this.epubBook.package.metadata.direction === 'rtl' ?
                this.epubRendition.next() : this.epubRendition.prev()
            if (e) e.preventDefault()
        },
        next: function(e) {
            if (!this.epubRendition) return
            this.epubBook.package.metadata.direction === 'rtl' ?
                this.epubRendition.prev() : this.epubRendition.next()
            if (e) e.preventDefault()
        },
        gotoToc: function(toc) {
            if (!this.epubRendition) return
            this.epubRendition.display(toc.href)
        },
        onThumbError: function() {
            // Use MIME icon fallback
        },
        onResize: function() {
            if (!this.loading || this.loaded) return

            var coverEl = document.getElementById('cover')
            if (!coverEl) return

            var style = getFrame(coverEl, true)
            var rate = parseFloat(style.width) / parseFloat(style.height)

            this.coverStyle = this.getCoverStyle(rate, this.$refs.epubWrapper, false)
            this.coverShadowStyle = this.getCoverStyle(rate, this.$refs.epubWrapper, false)
        }
    }
})
