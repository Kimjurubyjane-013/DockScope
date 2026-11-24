import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseButton from '@/components/common/BaseButton.vue'

describe('BaseButton', () => {
  it('renders slot content correctly', () => {
    const wrapper = mount(BaseButton, {
      slots: {
        default: 'Execute Action',
      },
    })
    expect(wrapper.text()).toContain('Execute Action')
  })

  it('applies primary variant classes by default', () => {
    const wrapper = mount(BaseButton)
    expect(wrapper.classes()).toContain('bg-dock-primary')
  })

  it('renders disabled state when disabled prop is true', () => {
    const wrapper = mount(BaseButton, {
      props: {
        disabled: true,
      },
    })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('displays loading spinner when loading prop is true', () => {
    const wrapper = mount(BaseButton, {
      props: {
        loading: true,
      },
    })
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
    expect(wrapper.attributes('disabled')).toBeDefined()
  })
})
