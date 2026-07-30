/**
 * PDF 查看器组件
 * Props:
 *   - url: PDF 文件的下载地址
 *   - init-scale: 初始缩放比例，默认 1.5
 * Events:
 *   - loaded: PDF 加载完成，参数 { totalPages }
 *   - page-change: 页码变化，参数 { currentPage }
 *   - close: 用户请求关闭/返回
 */
Vue.component('pdf-viewer', {
    template: '\
    <div class="full-ab">\
        <div ref="pdfContainer" class="pdf-container"></div>\
        <div class="pdf-controls">\
            <button @click="zoomOut" :disabled="scale <= 0.5">&minus;</button>\
            <span class="zoom-info">{{ Math.round(scale * 100) }}%</span>\
            <button @click="zoomIn" :disabled="scale >= 5.0">+</button>\
            <button @click="prevPage" :disabled="currentPage <= 1">&lsaquo;</button>\
            <input type="number" v-model.number="currentPage" :min="1" :max="totalPages"\
                @change="goToPage" class="pdf-page-input">\
            <span class="page-info">/ {{ totalPages }}</span>\
            <button @click="nextPage" :disabled="currentPage >= totalPages">&rsaquo;</button>\
            <a v-bind:href="url" download class="pdf-download">下载</a>\
        </div>\
    </div>\
    ',
    props: {
        url: { type: String, required: true },
        initScale: { type: Number, default: 1.5 }
    },
    data: function() {
        return {
            loading: false,
            loaded: false,
            pdfDocument: null,
            currentPage: 1,
            totalPages: 0,
            scale: this.initScale
        }
    },
    watch: {
        url: function(newUrl) {
            if (newUrl) {
                this.loadPdf(newUrl)
            }
        },
        loaded: function(val) {
            this.$emit('loaded', { totalPages: this.totalPages, loaded: val })
        },
        currentPage: function(val) {
            this.$emit('page-change', { currentPage: val })
        }
    },
    mounted: function() {
        if (this.url) {
            this.loadPdf(this.url)
        }
    },
    beforeDestroy: function() {
        if (this.$refs.pdfContainer) {
            this.$refs.pdfContainer.removeEventListener('scroll', this.onScroll)
        }
        this.pdfDocument = null
    },
    methods: {
        loadPdf: function(url) {
            this.loading = true
            this.loaded = false
            this.pdfDocument = null
            this.currentPage = 1
            this.totalPages = 0

            if (typeof pdfjsLib === 'undefined') {
                console.error('PDF.js library not loaded')
                this.loading = false
                this.$emit('error', { message: 'PDF.js library not loaded' })
                return
            }

            var self = this
            pdfjsLib.getDocument(url).promise.then(function(pdfDoc) {
                self.pdfDocument = pdfDoc
                self.totalPages = pdfDoc.numPages
                self.loading = false
                self.loaded = true
                self.$nextTick(function() {
                    self.renderAllPages()
                    self.$refs.pdfContainer.addEventListener('scroll', self.onScroll)
                })
            }).catch(function(error) {
                console.error('Error loading PDF:', error)
                self.loading = false
                self.$emit('error', { message: error.message })
            })
        },
        renderAllPages: function() {
            if (!this.pdfDocument) return

            var container = this.$refs.pdfContainer
            if (!container) return

            container.innerHTML = ''
            var oldPage = this.currentPage
            var self = this

            function renderPage(pageNum) {
                return self.pdfDocument.getPage(pageNum).then(function(page) {
                    var viewport = page.getViewport({ scale: self.scale })
                    var canvas = document.createElement('canvas')
                    var context = canvas.getContext('2d')
                    canvas.height = viewport.height
                    canvas.width = viewport.width
                    canvas.className = 'pdf-page'
                    canvas.setAttribute('data-page', pageNum)

                    container.appendChild(canvas)

                    return page.render({
                        canvasContext: context,
                        viewport: viewport
                    }).promise
                })
            }

            var promises = []
            for (var i = 1; i <= this.totalPages; i++) {
                promises.push(renderPage(i))
            }

            Promise.all(promises).then(function() {
                self.$nextTick(function() {
                    self.scrollToPage(oldPage)
                })
            })
        },
        scrollToPage: function(pageNum) {
            var container = this.$refs.pdfContainer
            if (!container) return
            var target = container.querySelector('[data-page="' + pageNum + '"]')
            if (target) {
                target.scrollIntoView({ block: 'start' })
            }
        },
        onScroll: function() {
            var container = this.$refs.pdfContainer
            if (!container) return
            var pages = container.querySelectorAll('.pdf-page')
            var containerMid = container.scrollTop + container.clientHeight / 2

            for (var i = 0; i < pages.length; i++) {
                var page = pages[i]
                var pageTop = page.offsetTop
                var pageBottom = pageTop + page.offsetHeight
                if (containerMid >= pageTop && containerMid < pageBottom) {
                    this.currentPage = parseInt(page.getAttribute('data-page'))
                    break
                }
            }
        },
        prevPage: function() {
            if (this.currentPage > 1) {
                this.scrollToPage(this.currentPage - 1)
            }
        },
        nextPage: function() {
            if (this.currentPage < this.totalPages) {
                this.scrollToPage(this.currentPage + 1)
            }
        },
        zoomIn: function() {
            this.scale = Math.min(this.scale + 0.25, 5.0)
            this.renderAllPages()
        },
        zoomOut: function() {
            this.scale = Math.max(this.scale - 0.25, 0.5)
            this.renderAllPages()
        },
        goToPage: function(e) {
            var value = parseInt(e.target.value)
            if (!isNaN(value) && value >= 1 && value <= this.totalPages) {
                this.scrollToPage(value)
            } else {
                e.target.value = this.currentPage
            }
        }
    }
})
