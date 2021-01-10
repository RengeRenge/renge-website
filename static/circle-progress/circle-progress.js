Vue.component('circle-progress', {
    props: ['plan', 'text', 'width', 'height', 'fontsize', 'circle'],
    data() {
        return {
            animate_delay: 0.5
        };
    },
    watch: {
        plan: function (val) {
            this.planChange();
        },
    },
    mounted() {
        this.planChange();
    },
    methods: {
        planChange() {
            if (this.plan > 50 && this.plan <= 100) {
                this.$refs["semicircle-l"].style.transform = `rotate(${(this.plan -
                    50) *
                3.6}deg)`;
            }
            if (this.plan > 100) {
                this.$refs["semicircle-l"].style.transform = `rotate(180deg)`;
            }
            if (this.plan < 50) {
                this.$refs["semicircle-r"].style.transform = `rotate(${this.plan * 3.6}deg)`;
                this.animate_delay = 0.5
            } else {
                this.$refs["semicircle-r"].style.transform = `rotate(180deg)`;
                if (this.animate_delayTimer || this.animate_delay === 0) {
                    return
                }
                this.animate_delayTimer = setTimeout(()=>{
                    this.animate_delayTimer = 0
                    if (this.plan >= 50) {
                        this.animate_delay = 0
                    }
                }, 500)
            }
        }
    },
    template: `
    <div class="overall">
    <div class="annulus-box" v-bind:style="{width:width+'px', height:height+'px'}">
      <div class="plan" v-bind:style="{width:width*0.75+'px', height:height*0.75+'px', fontSize: fontsize?fontsize:'inherit', left: 'calc(50% - ' + width*0.375 +'px', top: 'calc(50% - ' + height*0.375 +'px'}">
          <span>{{text}}</span>
      </div>
      <div class="annulus-bck" v-bind:style="circle">
        <div class="annulus-left">
          <div ref="semicircle-l" class="semicircle" v-bind:style="{width:width+'px', transitionDelay: animate_delay +'s'}"></div>
        </div>
        <div class="annulus-right">
          <div ref="semicircle-r" class="semicircle" v-bind:style="{width:width+'px'}"></div>
        </div>
      </div>
    </div>
  </div>`
})

Vue.component('bar-progress', {
    props: ['progress', 'height', 'fillColor', 'bgColor', 'text', 'textStyle', 'textCenter'],
    template:`
<div v-bind:style="{display: 'flex', flexDirection: 'column', alignItems: textCenter ? 'center' : 'auto'}">
    <div class="bar-progress" v-bind:style="{borderRadius: height/2+'px', height: height+'px', border: fillColor + ' solid 1px', backgroundColor: bgColor}">
        <div class="bar-content" v-bind:style="{width:Math.min(progress,100)+'%', backgroundColor: fillColor}"></div>
    </div>
    <a class="bar-text" v-bind:style="textStyle">{{text}}</a>
</div>`
})