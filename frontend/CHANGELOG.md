## [1.0.1](https://github.com/dkage/cyber-beacon/compare/v1.0.0...v1.0.1) (2026-11-24)


### Bug Fixes

* **ci:** exclude the generated release changelog ([c4147ba](https://github.com/dkage/cyber-beacon/commit/c4147ba39cfb0839e78ec0f88741d5746f21d471)), closes [#63](https://github.com/dkage/cyber-beacon/issues/63) [#65](https://github.com/dkage/cyber-beacon/issues/65) [#70](https://github.com/dkage/cyber-beacon/issues/70)
* **ci:** keep quality checks within their intended scope ([8ac9f12](https://github.com/dkage/cyber-beacon/commit/8ac9f12f2e21b6fd7306e65ff71afd92031a7a25)), closes [#63](https://github.com/dkage/cyber-beacon/issues/63) [#69](https://github.com/dkage/cyber-beacon/issues/69) [#70](https://github.com/dkage/cyber-beacon/issues/70)
* **kiosk:** reject malformed day summaries ([52800d6](https://github.com/dkage/cyber-beacon/commit/52800d69ffab8afdcbfe08d19946a84920657db5)), closes [#65](https://github.com/dkage/cyber-beacon/issues/65)

# 1.0.0 (2026-11-19)


### Bug Fixes

* address phase-one refresh and browsing review ([4d7de36](https://github.com/dkage/cyber-beacon/commit/4d7de361a49b230f8eaaac475dcce644743db86c)), closes [#14](https://github.com/dkage/cyber-beacon/issues/14) [#15](https://github.com/dkage/cyber-beacon/issues/15) [#19](https://github.com/dkage/cyber-beacon/issues/19) [#32](https://github.com/dkage/cyber-beacon/issues/32) [#33](https://github.com/dkage/cyber-beacon/issues/33)
* **api:** describe response and restore contracts ([54630b6](https://github.com/dkage/cyber-beacon/commit/54630b6f631205a9acd280eba5d6e4b85417a305)), closes [#11](https://github.com/dkage/cyber-beacon/issues/11) [#14](https://github.com/dkage/cyber-beacon/issues/14) [#19](https://github.com/dkage/cyber-beacon/issues/19)
* **backend:** verify read models and worker isolation ([6e13887](https://github.com/dkage/cyber-beacon/commit/6e13887c64a46cfaa45c3350d8369e3d5822d5fa)), closes [#8](https://github.com/dkage/cyber-beacon/issues/8) [#11](https://github.com/dkage/cyber-beacon/issues/11) [#16](https://github.com/dkage/cyber-beacon/issues/16) [#17](https://github.com/dkage/cyber-beacon/issues/17) [#18](https://github.com/dkage/cyber-beacon/issues/18) [#19](https://github.com/dkage/cyber-beacon/issues/19)
* **domain:** enforce ownership inside service boundaries ([4247073](https://github.com/dkage/cyber-beacon/commit/424707328f457350859a799b576686bc0711ac69)), closes [#10](https://github.com/dkage/cyber-beacon/issues/10) [#11](https://github.com/dkage/cyber-beacon/issues/11) [#14](https://github.com/dkage/cyber-beacon/issues/14) [#15](https://github.com/dkage/cyber-beacon/issues/15)
* **frontend:** clear stale integration selections ([b6b441c](https://github.com/dkage/cyber-beacon/commit/b6b441ca0d8a1d6861ceb3a4af966ef5c4af5a36)), closes [#13](https://github.com/dkage/cyber-beacon/issues/13) [#31](https://github.com/dkage/cyber-beacon/issues/31) [#32](https://github.com/dkage/cyber-beacon/issues/32) [#33](https://github.com/dkage/cyber-beacon/issues/33)
* **frontend:** compact planner on short screens ([95c2d02](https://github.com/dkage/cyber-beacon/commit/95c2d025409e49770b708cc6b8f3a80c28b5a3ba)), closes [#30](https://github.com/dkage/cyber-beacon/issues/30)
* **frontend:** hide app navigation on login routes ([5bbc019](https://github.com/dkage/cyber-beacon/commit/5bbc0197ccb7e99610576eec34c3dd466f78f417)), closes [#8](https://github.com/dkage/cyber-beacon/issues/8)
* **frontend:** prevent empty-day viewport overflow ([be712db](https://github.com/dkage/cyber-beacon/commit/be712dbd5b9ae0c30b58f418aa30c096f63320f6)), closes [#30](https://github.com/dkage/cyber-beacon/issues/30)
* **integrations:** allow Google account selection ([ef087f3](https://github.com/dkage/cyber-beacon/commit/ef087f355c665af4dc21c5ba46c54876646cdef7)), closes [#31](https://github.com/dkage/cyber-beacon/issues/31)
* **integrations:** checkpoint throttled calendar pages ([96eceba](https://github.com/dkage/cyber-beacon/commit/96eceba2b4e19d443ae3c51cdbbac98622927ce5)), closes [#15](https://github.com/dkage/cyber-beacon/issues/15) [#16](https://github.com/dkage/cyber-beacon/issues/16) [#32](https://github.com/dkage/cyber-beacon/issues/32)
* **integrations:** guard provider auth updates ([7f9572b](https://github.com/dkage/cyber-beacon/commit/7f9572b80eba822240a448171564d18f6b78ca2d)), closes [#32](https://github.com/dkage/cyber-beacon/issues/32)
* **integrations:** label Google accounts by email ([87656e6](https://github.com/dkage/cyber-beacon/commit/87656e6ed1758efeb7239deb1b5ac98bf2514a17)), closes [#31](https://github.com/dkage/cyber-beacon/issues/31)
* **integrations:** localize Outlook all-day events ([7403470](https://github.com/dkage/cyber-beacon/commit/74034704800ccb4477e86635884ca81f5edb2b89)), closes [#32](https://github.com/dkage/cyber-beacon/issues/32)
* **integrations:** refresh and report Outlook calendars ([d0d87bf](https://github.com/dkage/cyber-beacon/commit/d0d87bf516adc284a88773265d8f6d8eb872ea70)), closes [#32](https://github.com/dkage/cyber-beacon/issues/32)
* **integrations:** scope import counts to repository Mounts ([691d84e](https://github.com/dkage/cyber-beacon/commit/691d84e82a52a81dffa286976f90173dc1b3217e)), closes [#33](https://github.com/dkage/cyber-beacon/issues/33)
* **integrations:** serialize refresh with disconnect ([d480cf4](https://github.com/dkage/cyber-beacon/commit/d480cf42ccb1c5aa166d55c3fd011416b3b5b777)), closes [#32](https://github.com/dkage/cyber-beacon/issues/32)
* invalidate calendar refresh leases on disconnect ([15aae93](https://github.com/dkage/cyber-beacon/commit/15aae933c4cc679a59f1f544b69c31c8f6c0f0e9)), closes [#11](https://github.com/dkage/cyber-beacon/issues/11) [#19](https://github.com/dkage/cyber-beacon/issues/19) [#32](https://github.com/dkage/cyber-beacon/issues/32)
* preserve last-good calendar data ([18f313e](https://github.com/dkage/cyber-beacon/commit/18f313e30eb0074faaac92a9ac9b8a186af36810)), closes [#11](https://github.com/dkage/cyber-beacon/issues/11) [#19](https://github.com/dkage/cyber-beacon/issues/19) [#32](https://github.com/dkage/cyber-beacon/issues/32)
* **security:** load Fernet keys from credential files ([7e0237d](https://github.com/dkage/cyber-beacon/commit/7e0237d022c3eb8e4e40a8daee7bcfa239ed9993)), closes [#32](https://github.com/dkage/cyber-beacon/issues/32)


### Features

* **frontend:** build the first usable day planner ([5b17f76](https://github.com/dkage/cyber-beacon/commit/5b17f76759e74273fd8b9dbd77fafc82b65618a7)), closes [#9](https://github.com/dkage/cyber-beacon/issues/9) [#12](https://github.com/dkage/cyber-beacon/issues/12) [#13](https://github.com/dkage/cyber-beacon/issues/13) [#14](https://github.com/dkage/cyber-beacon/issues/14) [#15](https://github.com/dkage/cyber-beacon/issues/15) [#16](https://github.com/dkage/cyber-beacon/issues/16) [#17](https://github.com/dkage/cyber-beacon/issues/17) [#19](https://github.com/dkage/cyber-beacon/issues/19)
* **frontend:** open task editor in a modal ([67909a5](https://github.com/dkage/cyber-beacon/commit/67909a576b6bd44cb717c33cae3f7de3a5e19ddf)), closes [#30](https://github.com/dkage/cyber-beacon/issues/30)
* **integrations:** add GitHub Issues source ([071ca8b](https://github.com/dkage/cyber-beacon/commit/071ca8b100088ccc1e6e1be0cb21902f9e6add4c)), closes [#33](https://github.com/dkage/cyber-beacon/issues/33)
* **integrations:** add imports and read-only calendars ([f31c7fd](https://github.com/dkage/cyber-beacon/commit/f31c7fdd0093a67f31aca630abfbe02c2e953d77)), closes [#14](https://github.com/dkage/cyber-beacon/issues/14) [#15](https://github.com/dkage/cyber-beacon/issues/15) [#16](https://github.com/dkage/cyber-beacon/issues/16) [#19](https://github.com/dkage/cyber-beacon/issues/19)
* **integrations:** add Outlook Calendar ([ede0193](https://github.com/dkage/cyber-beacon/commit/ede0193a7726e410813efdbe5235dc77e3e4cdb2)), closes [#32](https://github.com/dkage/cyber-beacon/issues/32)
* **planner:** add versioned tasks and daily execution ([721dda3](https://github.com/dkage/cyber-beacon/commit/721dda3eb9d3552342f2057ed9e9457ee9ad9ef3)), closes [#10](https://github.com/dkage/cyber-beacon/issues/10) [#11](https://github.com/dkage/cyber-beacon/issues/11) [#12](https://github.com/dkage/cyber-beacon/issues/12) [#16](https://github.com/dkage/cyber-beacon/issues/16) [#17](https://github.com/dkage/cyber-beacon/issues/17) [#18](https://github.com/dkage/cyber-beacon/issues/18)
* **settings:** add preferred date format ([a82b6eb](https://github.com/dkage/cyber-beacon/commit/a82b6eb355e26fee7349be21802f168af8e53423)), closes [#29](https://github.com/dkage/cyber-beacon/issues/29)
